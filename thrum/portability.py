"""Explicit, private export/import and consistent backups; never overwrite."""
import json
import os
import sqlite3
import uuid
from .storage import contact_values, private_path, text, MAX_REVISION


def export_data(store):
    store.con.execute('BEGIN')
    try:
        return {'format': 'thrum', 'version': 1, 'contacts': store.list_contacts(),
                'relationships': store.relationships()}
    finally:
        store.con.execute('ROLLBACK')


def identifier(value):
    if not isinstance(value, str): raise ValueError('Invalid stable identifier.')
    try:
        if str(uuid.UUID(value)) != value: raise ValueError()
    except ValueError: raise ValueError('Invalid stable identifier.') from None
    return value


def revision(value):
    if type(value) is not int or not 1 <= value <= MAX_REVISION: raise ValueError('Invalid revision.')
    return value


def import_data(store, data):
    """Import only into an empty store, preserving IDs; all-or-nothing."""
    if not isinstance(data, dict) or set(data) != {'format', 'version', 'contacts', 'relationships'}:
        raise ValueError('Invalid Thrum export.')
    if data['format'] != 'thrum' or type(data['version']) is not int or data['version'] != 1:
        raise ValueError('Unsupported export format or version.')
    if any(not isinstance(data[k], list) or len(data[k]) > 100000 for k in ('contacts', 'relationships')):
        raise ValueError('Invalid export collections.')
    try:
        with store.transaction():
            if store.con.execute('SELECT count(*) FROM contacts').fetchone()[0]:
                raise ValueError('Import requires an empty database; use a new database path.')
            for c in data['contacts']:
                if not isinstance(c, dict) or set(c) != {'id','kind','name','affiliation','methods','tags','notes','revision'}:
                    raise ValueError('Invalid contact fields.')
                v = contact_values(c)
                store.con.execute('INSERT INTO contacts VALUES (?,?,?,?,?,?,?,?)',
                    (identifier(c['id']),v['kind'],v['name'],v['affiliation'],json.dumps(v['methods'],ensure_ascii=False),
                     json.dumps(v['tags'],ensure_ascii=False),v['notes'],revision(c['revision'])))
            for edge in data['relationships']:
                if not isinstance(edge, dict) or set(edge) != {'id','source','target','type','notes','revision'}:
                    raise ValueError('Invalid relationship fields.')
                store.con.execute('INSERT INTO relationships VALUES (?,?,?,?,?,?)',
                    (identifier(edge['id']),identifier(edge['source']),identifier(edge['target']),
                     text(edge['type'],required=True,limit=100),text(edge['notes']),revision(edge['revision'])))
    except sqlite3.IntegrityError:
        raise ValueError('Import contains duplicate IDs or missing relationship endpoints.') from None


def create_output(path):
    path = private_path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return path, fd


def write_export(store, path):
    data = json.dumps(export_data(store), ensure_ascii=False, indent=2) + '\n'
    path, fd = create_output(path)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(data)
            stream.flush(); os.fsync(stream.fileno())
    except BaseException:
        path.unlink()
        raise


def backup(store, path):
    path, fd = create_output(path)
    os.close(fd)
    try:
        target = sqlite3.connect(path)
        try:
            store.con.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Backup integrity check failed.')
        finally:
            target.close()
    except BaseException:
        path.unlink()
        raise
