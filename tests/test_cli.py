import json
import errno
import http.client
import io
import os
from pathlib import Path
import re
import select
import socket
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from thrum.__main__ import main


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.db=self.root/'demo.sqlite'

    def run_cli(self,*args,db=None):
        return subprocess.run([sys.executable,'-B','-m','thrum','--db',str(db or self.db),*args],capture_output=True,text=True,timeout=10)

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

    def test_serve_automatically_uses_free_port_when_default_is_busy(self):
        self.assertEqual(self.run_cli('init').returncode,0)
        with socket.socket() as occupied:
            try:
                occupied.bind(('127.0.0.1',8765))
                occupied.listen()
            except OSError as error:
                if error.errno != errno.EADDRINUSE: raise
            process=subprocess.Popen(
                [sys.executable,'-B','-m','thrum','--db',str(self.db),'serve'],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                ready,_,_=select.select([process.stdout],[],[],10)
                self.assertTrue(ready,'Server did not report its URL within 10 seconds')
                line=process.stdout.readline()
                match=re.search(r'http://127\.0\.0\.1:(\d+)/',line)
                self.assertIsNotNone(match,f'Server did not start: {line!r}')
                port=int(match.group(1))
                self.assertNotEqual(port,8765)
                connection=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
                try:
                    connection.request('GET','/')
                    response=connection.getresponse()
                    self.assertEqual(response.status,200)
                    response.read()
                finally:
                    connection.close()
            finally:
                process.terminate()
                process.communicate(timeout=5)

    def test_explicit_busy_port_reports_conflict_without_switching(self):
        self.assertEqual(self.run_cli('init').returncode,0)
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1',0));occupied.listen()
            port=occupied.getsockname()[1]
            result=self.run_cli('serve','--port',str(port))
        self.assertEqual(result.returncode,1)
        self.assertIn(str(port),result.stderr)
        self.assertIn('already in use',result.stderr)
        self.assertNotIn('database integrity',result.stderr)

    def test_serve_does_not_retry_unrelated_errors(self):
        self.assertEqual(self.run_cli('init').returncode,0)
        errors=io.StringIO()
        with patch('thrum.web.Server',side_effect=PermissionError(errno.EACCES,'private-path')) as server:
            with redirect_stderr(errors):
                self.assertEqual(main(['--db',str(self.db),'serve']),1)
        self.assertEqual(server.call_count,1)
        self.assertNotIn('private-path',errors.getvalue())

    def test_errors_do_not_echo_private_file_names(self):
        r=self.run_cli('import',str(self.root/'sensitive-example.json'))
        self.assertNotEqual(r.returncode,0)
        self.assertNotIn('sensitive-example',r.stderr)
