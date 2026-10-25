import copy
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from thrum.storage import Store
from thrum.portability import export_data, import_data, backup, write_export


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.store = Store(self.root / 'people.sqlite')
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.store.close)

    def person(self, **changes):
        return self.store.save_contact(dict(kind='person', name='Example Person',
            affiliation='Imaginary Observatory', methods=[{'kind': 'email', 'value': 'demo@example.invalid', 'label': 'work'}],
            tags=['science'], notes='Fictional fixture', **changes))

    def test_duplicate_names_have_stable_distinct_ids(self):
        a, b = self.person(), self.person()
        self.assertNotEqual(a['id'], b['id'])
        a['name'] = 'Renamed Example'
        self.store.save_contact(a, a['id'])
        self.assertEqual(self.store.get_contact(a['id'])['name'], 'Renamed Example')
        self.assertEqual(self.store.get_contact(b['id'])['name'], 'Example Person')

    def test_contact_delete_cascades_relationships(self):
        a, b = self.person(), self.person()
        self.store.save_relationship(dict(source=a['id'], target=b['id'], type='introduced', notes='Fictional'))
        self.store.delete_contact(a['id'])
        self.assertEqual(self.store.relationships(b['id']), [])
        with self.assertRaises(KeyError): self.store.get_contact(a['id'])

    def test_relationship_crud_and_direction(self):
        a, b = self.person(), self.person()
        edge = self.store.save_relationship(dict(source=a['id'], target=b['id'], type='colleague', notes='Initial'))
        self.assertEqual(self.store.relationships(b['id'])[0]['source'], a['id'])
        edge['notes'] = 'Updated'
        edge['type'] = 'introduced'
        self.store.save_relationship(edge, edge['id'])
        self.assertEqual(self.store.relationships(a['id'])[0]['notes'], 'Updated')
        self.store.delete_relationship(edge['id'])
        self.assertEqual(self.store.relationships(a['id']), [])

    def test_missing_relationship_endpoint_rejected(self):
        a = self.person()
        with self.assertRaises(ValueError):
            self.store.save_relationship(dict(source=a['id'], target='missing', type='knows', notes=''))
        self.assertEqual(self.store.relationships(a['id']), [])

    def test_search_all_fields_and_filter(self):
        self.person()
        org = self.store.save_contact(dict(name='Invented Guild', kind='organization'))
        for query in ['EXAMPLE PERSON', 'observatory', 'demo@example.invalid', 'science']:
            with self.subTest(query=query): self.assertEqual(len(self.store.list_contacts(query)), 1)
        self.assertEqual(self.store.list_contacts(kind='organization')[0]['id'], org['id'])
        self.assertEqual(len(self.store.list_contacts(tag='SCIENCE')), 1)
        self.assertEqual(self.store.list_contacts("%' OR 1=1 --"), [])
        self.assertEqual(self.store.list_contacts('%'), [])

    def test_invalid_contact_is_atomic(self):
        a = self.person()
        for change in [{'name': ' '}, {'kind': 'other'}, {'tags': 'bad'}, {'methods': [{'kind': 'email'}]}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.store.save_contact({**a, **change}, a['id'])
        self.assertEqual(self.store.get_contact(a['id'])['name'], 'Example Person')

    def test_stale_edit_rejected(self):
        a = self.person()
        self.store.save_contact({**a, 'name': 'New'}, a['id'])
        with self.assertRaises(ValueError): self.store.save_contact(a, a['id'])

    def test_initialization_is_repeatable_and_private(self):
        a = self.person()
        self.store.close()
        self.store = Store(self.root / 'people.sqlite')
        self.addCleanup(self.store.close)
        self.assertEqual(self.store.get_contact(a['id'])['name'], 'Example Person')
        self.assertEqual(self.store.con.execute('PRAGMA user_version').fetchone()[0], 2)
        if os.name == 'posix': self.assertEqual((self.root / 'people.sqlite').stat().st_mode & 0o777, 0o600)

    def test_future_schema_refused_without_change(self):
        self.store.con.execute('PRAGMA user_version=99')
        self.store.close()
        before = (self.root / 'people.sqlite').read_bytes()
        with self.assertRaises(ValueError): Store(self.root / 'people.sqlite')
        self.assertEqual((self.root / 'people.sqlite').read_bytes(), before)

    def test_version_one_migrates_without_losing_contacts(self):
        a = self.person()
        self.store.con.execute('DROP TABLE relationships')
        self.store.con.execute('PRAGMA user_version=1')
        self.store.close()
        self.store = Store(self.root / 'people.sqlite')
        self.addCleanup(self.store.close)
        self.assertEqual(self.store.get_contact(a['id'])['name'], 'Example Person')
        self.assertEqual(self.store.relationships(a['id']), [])

    def test_rejects_checkout_paths_and_symlinks(self):
        checkout = self.root / 'repo'; checkout.mkdir(); (checkout / '.git').mkdir()
        with self.assertRaises(ValueError): Store(checkout / 'data' / 'people.sqlite')
        alias = self.root / 'alias.sqlite'; alias.symlink_to(self.root / 'people.sqlite')
        with self.assertRaises(ValueError): Store(alias)

    def test_unrelated_database_refused(self):
        p = self.root / 'unrelated.sqlite'
        with sqlite3.connect(p) as c: c.execute('CREATE TABLE other(value)')
        p.chmod(0o600)
        with self.assertRaises(ValueError): Store(p)

    def test_export_import_roundtrip_preserves_ids(self):
        a, b = self.person(), self.person()
        self.store.save_relationship(dict(source=a['id'], target=b['id'], type='knows', notes='Demo'))
        data = export_data(self.store)
        other = Store(self.root / 'other.sqlite'); self.addCleanup(other.close)
        import_data(other, data)
        self.assertEqual(export_data(other), data)
        with self.assertRaises(ValueError): import_data(other, data)

    def test_invalid_import_rolls_back_everything(self):
        a, b = self.person(), self.person()
        self.store.save_relationship(dict(source=a['id'], target=b['id'], type='knows'))
        data = export_data(self.store)
        other = Store(self.root / 'other.sqlite'); self.addCleanup(other.close)
        bad = copy.deepcopy(data); bad['relationships'][0]['target'] = 'missing'
        with self.assertRaises(ValueError): import_data(other, bad)
        self.assertEqual(other.list_contacts(), [])
        bad = copy.deepcopy(data); bad['version'] = 999
        with self.assertRaises(ValueError): import_data(other, bad)
        bad = copy.deepcopy(data); bad['contacts'].append(bad['contacts'][0])
        with self.assertRaises(ValueError): import_data(other, bad)
        self.assertEqual(other.list_contacts(), [])

    def test_consistent_backup_and_no_overwrites(self):
        self.person(); p = self.root / 'backup.sqlite'
        backup(self.store, p)
        other = Store(p); self.addCleanup(other.close)
        self.assertEqual(export_data(other), export_data(self.store))
        self.assertEqual(other.con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        with self.assertRaises(FileExistsError): backup(self.store, p)
        out = self.root / 'export.json'; write_export(self.store, out)
        with self.assertRaises(FileExistsError): write_export(self.store, out)
        if os.name == 'posix': self.assertEqual(out.stat().st_mode & 0o777, 0o600)

    def test_import_rejects_out_of_range_revisions_atomically(self):
        self.person();data=export_data(self.store)
        other=Store(self.root/'other.sqlite');self.addCleanup(other.close)
        for value in [True, 0, -1, 2**63, 1.5, '1']:
            bad=copy.deepcopy(data);bad['contacts'][0]['revision']=value
            with self.subTest(value=value), self.assertRaises(ValueError): import_data(other,bad)
            self.assertEqual(other.list_contacts(),[])

    def test_exhausted_revisions_cannot_change_type(self):
        a=self.person()
        self.store.con.execute('UPDATE contacts SET revision=? WHERE id=?',(2**63-1,a['id']))
        a=self.store.get_contact(a['id'])
        with self.assertRaises(ValueError): self.store.save_contact({**a,'name':'Changed'},a['id'])
        self.assertEqual(self.store.get_contact(a['id'])['name'],'Example Person')

    def test_backup_excludes_uncommitted_concurrent_writes(self):
        a=self.person()
        writer=sqlite3.connect(self.store.path);self.addCleanup(writer.close)
        writer.execute('BEGIN IMMEDIATE')
        writer.execute('UPDATE contacts SET name=? WHERE id=?',('Uncommitted',a['id']))
        p=self.root/'concurrent.sqlite';backup(self.store,p)
        writer.rollback()
        other=Store(p);self.addCleanup(other.close)
        self.assertEqual(other.get_contact(a['id'])['name'],'Example Person')

    def test_relationship_revision_overflow_refused(self):
        a,b=self.person(),self.person()
        edge=self.store.save_relationship(dict(source=a['id'],target=b['id'],type='knows'))
        self.store.con.execute('UPDATE relationships SET revision=? WHERE id=?',(2**63-1,edge['id']))
        edge=self.store.get_relationship(edge['id'])
        with self.assertRaises(ValueError): self.store.save_relationship({**edge,'notes':'Changed'},edge['id'])
        self.assertEqual(self.store.get_relationship(edge['id'])['notes'],'')
