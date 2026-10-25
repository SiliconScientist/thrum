import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.db=self.root/'demo.sqlite'

    def run_cli(self,*args,db=None):
        return subprocess.run([sys.executable,'-B','-m','thrum','--db',str(db or self.db),*args],capture_output=True,text=True)

    def test_quickstart_and_portability_commands(self):
        for args in [('init',),('demo',),('check',)]:
            r=self.run_cli(*args);self.assertEqual(r.returncode,0,r.stderr)
        export=self.root/'export.json';backup=self.root/'backup.sqlite'
        self.assertEqual(self.run_cli('export',str(export)).returncode,0)
        data=json.loads(export.read_text());self.assertEqual(len(data['contacts']),4);self.assertEqual(len(data['relationships']),3)
        self.assertEqual(self.run_cli('backup',str(backup)).returncode,0)
        self.assertEqual(self.run_cli('check',db=backup).returncode,0)
        restored=self.root/'restored.sqlite'
        self.assertEqual(self.run_cli('import',str(export),db=restored).returncode,0)
        again=self.root/'again.json';self.assertEqual(self.run_cli('export',str(again),db=restored).returncode,0)
        self.assertEqual(json.loads(again.read_text()),data)
        self.assertNotEqual(self.run_cli('import',str(export)).returncode,0)
        self.assertNotEqual(self.run_cli('demo').returncode,0)

    def test_rejects_duplicate_json_keys_and_unsafe_paths(self):
        source=self.root/'bad.json';source.write_text('{"version":1,"version":2}');source.chmod(0o600)
        r=self.run_cli('import',str(source));self.assertNotEqual(r.returncode,0)
        self.assertNotIn('Traceback',r.stderr)
        repo=self.root/'repo';repo.mkdir();(repo/'.git').mkdir()
        r=self.run_cli('init',db=repo/'data.sqlite');self.assertNotEqual(r.returncode,0)
        self.assertFalse((repo/'data.sqlite').exists())

    def test_check_does_not_create_missing_database(self):
        self.assertNotEqual(self.run_cli('check').returncode,0)
        self.assertFalse(self.db.exists())

    def test_errors_do_not_echo_private_file_names(self):
        r=self.run_cli('import',str(self.root/'sensitive-example.json'))
        self.assertNotEqual(r.returncode,0)
        self.assertNotIn('sensitive-example',r.stderr)
