"""Private SQLite storage. No network access or personal-data logging."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import stat
import uuid

APPLICATION_ID = 0x5448524D
MAX_REVISION = 2**63 - 1
MIGRATIONS = {
    1: ["""CREATE TABLE contacts (
        id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('person','organization')),
        name TEXT NOT NULL, affiliation TEXT NOT NULL, methods TEXT NOT NULL,
        tags TEXT NOT NULL, notes TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1)"""],
    2: ["""CREATE TABLE relationships (
        id TEXT PRIMARY KEY, source TEXT NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
        target TEXT NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
        type TEXT NOT NULL, notes TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1)""",
        'CREATE INDEX relationships_source ON relationships(source)',
        'CREATE INDEX relationships_target ON relationships(target)'],
}


def default_path():
    return Path.home() / '.local' / 'share' / 'thrum' / 'people.sqlite'


def private_path(path):
    """Only private, non-symlink files outside any Git checkout are allowed.

    Existing directories are never chmodded. Users choose a dedicated directory.
    This guards accidental disclosure, not hostile processes running as this user.
    """
    path = Path(path).expanduser().absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('Choose a path without symbolic links.')
    for parent in path.parents:
        if parent.name == '.git' or (parent / '.git').exists():
            raise ValueError('Private data must be outside Git checkouts.')
    if not path.parent.exists():
        path.parent.mkdir(parents=True, mode=0o700)
    parent = path.parent.stat()
    if os.name == 'posix' and (parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) & 0o077):
        raise ValueError('Choose a private directory owned by you with permissions 0700.')
    if path.exists():
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('Private data must be a regular file with one link.')
        if os.name == 'posix' and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
            raise ValueError('Private files must be owned by you with permissions 0600.')
    return path


def text(value, *, required=False, limit=20000):
    if not isinstance(value, str) or '\x00' in value or len(value) > limit:
        raise ValueError('Text is invalid or too long.')
    value = value.strip()
    if required and not value:
        raise ValueError('Required fields cannot be empty.')
    return value


def contact_values(data):
    if not isinstance(data, dict): raise ValueError('Expected a contact object.')
    kind = data.get('kind', 'person')
    if kind not in ('person', 'organization'): raise ValueError('Choose person or organization.')
    tags = data.get('tags', [])
    methods = data.get('methods', [])
    if not isinstance(tags, list) or len(tags) > 100: raise ValueError('Invalid tags.')
    tags = list(dict.fromkeys(text(t, required=True, limit=100) for t in tags))
    if not isinstance(methods, list) or len(methods) > 100: raise ValueError('Invalid contact methods.')
    normalized = []
    for method in methods:
        if not isinstance(method, dict) or set(method) - {'kind', 'value', 'label'}:
            raise ValueError('Invalid contact method.')
        normalized.append(dict(kind=text(method.get('kind'), required=True, limit=100),
            value=text(method.get('value'), required=True, limit=1000),
            label=text(method.get('label', ''), limit=100)))
    return dict(kind=kind, name=text(data.get('name'), required=True, limit=300),
        affiliation=text(data.get('affiliation', ''), limit=1000), methods=normalized,
        tags=tags, notes=text(data.get('notes', '')))


class Store:
    def __init__(self, path=None):
        self.path = private_path(path if path is not None else default_path())
        for suffix in ('-journal', '-wal', '-shm'):
            sidecar = Path(str(self.path) + suffix)
            if sidecar.exists() or sidecar.is_symlink(): private_path(sidecar)
        new = not self.path.exists()
        if new:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        self.con = sqlite3.connect(self.path, isolation_level=None, timeout=5)
        self.con.row_factory = sqlite3.Row
        try:
            version = self.con.execute('PRAGMA user_version').fetchone()[0]
            app = self.con.execute('PRAGMA application_id').fetchone()[0]
            if not new and (app != APPLICATION_ID or not 1 <= version <= len(MIGRATIONS)):
                raise ValueError('Unrecognized database or unsupported schema version.')
            self.con.execute('PRAGMA foreign_keys=ON')
            self.con.execute('PRAGMA secure_delete=ON')
            with self.transaction():
                for n in range(version + 1, len(MIGRATIONS) + 1):
                    for statement in MIGRATIONS[n]: self.con.execute(statement)
                    self.con.execute(f'PRAGMA user_version={n}')
                self.con.execute(f'PRAGMA application_id={APPLICATION_ID}')
        except BaseException:
            self.con.close()
            raise

    def close(self):
        self.con.close()

    @contextmanager
    def transaction(self):
        self.con.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.con.execute('COMMIT')
        except BaseException:
            self.con.execute('ROLLBACK')
            raise

    @staticmethod
    def decode(row):
        value = dict(row)
        if 'methods' in value:
            value['methods'] = json.loads(value['methods'])
            value['tags'] = json.loads(value['tags'])
        return value

    def get_contact(self, identifier):
        row = self.con.execute('SELECT * FROM contacts WHERE id=?', (identifier,)).fetchone()
        if row is None: raise KeyError('Contact not found.')
        return self.decode(row)

    def list_contacts(self, query='', kind='', tag=''):
        if kind not in ('', 'person', 'organization'): raise ValueError('Invalid contact filter.')
        query, tag = query.casefold().strip(), tag.casefold().strip()
        result = []
        for row in self.con.execute('SELECT * FROM contacts ORDER BY name COLLATE NOCASE,id'):
            c = self.decode(row)
            fields = [c['name'], c['affiliation'], *c['tags'], *(m['value'] for m in c['methods'])]
            if kind and kind != c['kind']: continue
            if tag and tag not in [t.casefold() for t in c['tags']]: continue
            if query and not any(query in field.casefold() for field in fields): continue
            result.append(c)
        return result

    def save_contact(self, data, identifier=None):
        values = contact_values(data)
        values['methods'] = json.dumps(values['methods'], ensure_ascii=False)
        values['tags'] = json.dumps(values['tags'], ensure_ascii=False)
        with self.transaction():
            if identifier:
                current = self.get_contact(identifier)
                if current['revision'] >= MAX_REVISION: raise ValueError('Contact revision limit reached; no change saved.')
                if data.get('revision', current['revision']) != current['revision']:
                    raise ValueError('This contact changed. Reopen it before saving.')
                self.con.execute('UPDATE contacts SET kind=:kind,name=:name,affiliation=:affiliation,methods=:methods,tags=:tags,notes=:notes,revision=revision+1 WHERE id=:id', {**values, 'id': identifier})
            else:
                identifier = str(uuid.uuid4())
                self.con.execute('INSERT INTO contacts(id,kind,name,affiliation,methods,tags,notes) VALUES (:id,:kind,:name,:affiliation,:methods,:tags,:notes)', {**values, 'id': identifier})
        return self.get_contact(identifier)

    def delete_contact(self, identifier, revision=None):
        with self.transaction():
            current = self.get_contact(identifier)
            if revision is not None and revision != current['revision']: raise ValueError('Contact changed. Reopen before deleting.')
            self.con.execute('DELETE FROM contacts WHERE id=?', (identifier,))

    def relationships(self, identifier=None):
        sql = 'SELECT * FROM relationships'
        args = ()
        if identifier is not None:
            sql += ' WHERE source=? OR target=?'; args = (identifier, identifier)
        return [dict(row) for row in self.con.execute(sql + ' ORDER BY id', args)]

    def get_relationship(self, identifier):
        row = self.con.execute('SELECT * FROM relationships WHERE id=?', (identifier,)).fetchone()
        if row is None: raise KeyError('Relationship not found.')
        return dict(row)

    def save_relationship(self, data, identifier=None):
        values = dict(source=text(data.get('source'), required=True), target=text(data.get('target'), required=True),
            type=text(data.get('type'), required=True, limit=100), notes=text(data.get('notes', '')))
        with self.transaction():
            for endpoint in ('source', 'target'):
                try: self.get_contact(values[endpoint])
                except KeyError: raise ValueError('Choose existing contacts for both ends.') from None
            if identifier:
                current = self.get_relationship(identifier)
                if current['revision'] >= MAX_REVISION: raise ValueError('Relationship revision limit reached; no change saved.')
                if data.get('revision', current['revision']) != current['revision']:
                    raise ValueError('Relationship changed. Reopen before saving.')
                self.con.execute('UPDATE relationships SET source=:source,target=:target,type=:type,notes=:notes,revision=revision+1 WHERE id=:id', {**values, 'id': identifier})
            else:
                identifier = str(uuid.uuid4())
                self.con.execute('INSERT INTO relationships(id,source,target,type,notes) VALUES (:id,:source,:target,:type,:notes)', {**values, 'id': identifier})
        return self.get_relationship(identifier)

    def delete_relationship(self, identifier, revision=None):
        with self.transaction():
            current = self.get_relationship(identifier)
            if revision is not None and revision != current['revision']: raise ValueError('Relationship changed. Reopen before deleting.')
            self.con.execute('DELETE FROM relationships WHERE id=?', (identifier,))
