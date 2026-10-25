import contextlib
import http.client
import io
from pathlib import Path
import re
import tempfile
import threading
import unittest
from urllib.parse import urlencode

from thrum.storage import Store
from thrum.web import create_server


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name).resolve() / 'people.sqlite'
        store = Store(self.path)
        self.contact = store.save_contact(dict(name='Fictional <script>alert(1)</script>', kind='person'))
        self.org = store.save_contact(dict(name='Imaginary Society', kind='organization'))
        store.close()
        self.server = create_server(self.path, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.addCleanup(self.stop)
        self.host = '127.0.0.1:' + str(self.server.server_port)
        status, _, html = self.request('GET', '/contacts/new')
        self.assertEqual(status, 200)
        self.token = re.search(r'name="csrf" value="([^"]+)"', html).group(1)

    def stop(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()

    def request(self, method, path, fields=None, headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        body = None if fields is None else urlencode(fields)
        h = {'Host': self.host}
        if fields is not None: h.update({'Origin': 'http://' + self.host, 'Content-Type': 'application/x-www-form-urlencoded'})
        if headers: h.update(headers)
        c.request(method, path, body, h)
        r = c.getresponse(); result = (r.status, dict(r.getheaders()), r.read().decode()); c.close()
        return result

    def test_loopback_and_privacy_headers(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        code, headers, body = self.request('GET', '/')
        self.assertEqual(code, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertIn("default-src 'none'", headers['Content-Security-Policy'])
        self.assertIn('&lt;script&gt;', body)
        self.assertNotIn('<script>alert', body)
        self.assertNotIn('https://', body)

    def test_browser_contact_lifecycle(self):
        data = dict(csrf=self.token, name='Demo New', kind='person', affiliation='Imaginary Guild',
                    methods='email | new@example.invalid | work', tags='demo, science', notes='Invented')
        code, headers, _ = self.request('POST', '/contacts/new', data)
        self.assertEqual(code, 303); location = headers['Location']
        self.assertIn('Demo New', self.request('GET', location)[2])
        edit = self.request('GET', location + '/edit')[2]
        data['revision'] = re.search(r'name="revision" value="(\d+)"', edit).group(1)
        data['name'] = 'Demo Updated'
        self.assertEqual(self.request('POST', location + '/edit', data)[0], 303)
        delete = self.request('GET', location + '/delete')[2]
        revision = re.search(r'name="revision" value="(\d+)"', delete).group(1)
        self.assertEqual(self.request('POST', location + '/delete', dict(csrf=self.token, revision=revision, confirm='yes'))[0], 303)
        self.assertEqual(self.request('GET', location)[0], 404)

    def test_relationship_lifecycle_and_incoming(self):
        data = dict(csrf=self.token, source=self.contact['id'], target=self.org['id'], type='member of', notes='Fictional')
        code, headers, _ = self.request('POST', '/relationships/new', data)
        self.assertEqual(code, 303)
        with contextlib.closing(Store(self.path)) as s: edge = s.relationships()[0]
        page = self.request('GET', '/contacts/' + self.org['id'])[2]
        self.assertIn('Incoming', page); self.assertIn('member of', page)
        data.update(revision=edge['revision'], notes='Updated')
        self.assertEqual(self.request('POST', '/relationships/' + edge['id'] + '/edit', data)[0], 303)
        self.assertEqual(self.request('POST', '/relationships/' + edge['id'] + '/delete', dict(csrf=self.token,revision=2,confirm='yes'))[0], 303)
        with contextlib.closing(Store(self.path)) as s: self.assertEqual(s.relationships(), [])

    def test_cross_origin_requests_and_missing_csrf_rejected(self):
        for headers in [{'Host':'evil.invalid'}, {'Origin':'https://evil.invalid'}, {'Sec-Fetch-Site':'cross-site'}]:
            with self.subTest(headers=headers): self.assertEqual(self.request('GET', '/', headers=headers)[0], 403)
        data = dict(name='Must Not Exist', kind='person')
        for token in ['', 'wrong']:
            self.assertEqual(self.request('POST', '/contacts/new', {**data,'csrf':token})[0],403)
        self.assertEqual(self.request('POST','/contacts/new',{**data,'csrf':self.token}, {'Origin':'null'})[0],403)
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        c.request('POST','/contacts/new',urlencode({**data,'csrf':self.token}),{'Content-Type':'application/x-www-form-urlencoded'})
        r=c.getresponse(); self.assertEqual(r.status,403);r.read();c.close()
        with contextlib.closing(Store(self.path)) as s: self.assertEqual(s.list_contacts('Must Not Exist'),[])

    def test_duplicate_headers_and_fields_fail_closed(self):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        c.putrequest('GET','/');c.putheader('Host',self.host);c.endheaders()
        r=c.getresponse();self.assertEqual(r.status,403);r.read();c.close()
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        body=urlencode(dict(csrf=self.token,name='One',kind='person'))+'&name=Two'
        c.request('POST','/contacts/new',body,{'Origin':'http://'+self.host,'Content-Type':'application/x-www-form-urlencoded'})
        r=c.getresponse();self.assertEqual(r.status,400);r.read();c.close()

    def test_delete_requires_confirmation_and_revision(self):
        route='/contacts/'+self.contact['id']+'/delete'
        self.assertEqual(self.request('POST',route,dict(csrf=self.token,revision=1))[0],400)
        self.assertEqual(self.request('POST',route,dict(csrf=self.token,confirm='yes'))[0],400)
        self.assertEqual(self.request('GET','/contacts/'+self.contact['id'])[0],200)

    def test_malformed_routes_and_no_filesystem_serving(self):
        for path in ['/../../etc/passwd','/assets/../storage.py','/.git/config']:
            self.assertEqual(self.request('GET',path)[0],404)
        self.assertEqual(self.request('GET','/?q=%ZZ')[0],400)
        self.assertEqual(self.request('GET','/style.css')[0],200)

    def test_personal_data_not_logged(self):
        output=io.StringIO()
        with contextlib.redirect_stderr(output): self.request('GET','/?q=private-example')
        self.assertEqual(output.getvalue(),'')

    def test_edit_preserves_delimiters_in_importable_fields(self):
        import html
        with contextlib.closing(Store(self.path)) as s:
            c=s.save_contact(dict(name='Delimited Example',tags=['friends, family','line\nbreak'],
                methods=[{'kind':'chat','value':'a|b\nnext','label':'"quoted" label'}]))
        page=self.request('GET','/contacts/'+c['id']+'/edit')[2]
        methods=html.unescape(re.search(r'<textarea[^>]*name="methods"[^>]*>(.*?)</textarea>',page,re.S).group(1))
        tags=html.unescape(re.search(r'<textarea[^>]*name="tags"[^>]*>(.*?)</textarea>',page,re.S).group(1))
        data=dict(csrf=self.token,revision=1,name='Delimited Example',kind='person',methods=methods,tags=tags,notes='',affiliation='')
        self.assertEqual(self.request('POST','/contacts/'+c['id']+'/edit',data)[0],303)
        with contextlib.closing(Store(self.path)) as s:
            updated=s.get_contact(c['id'])
            self.assertEqual(updated['tags'],c['tags']);self.assertEqual(updated['methods'],c['methods'])

    def test_duplicate_names_have_distinct_relationship_labels(self):
        import html
        demo_path=Path(self.tmp.name).resolve()/'demo.sqlite'
        with contextlib.closing(Store(demo_path)) as store:
            for affiliation in ('Lantern Workshop','Imaginary Observatory'):
                store.save_contact(dict(name='Mira Example',kind='person',affiliation=affiliation))
            from thrum.views import relationship_form
            page=relationship_form('test-token',store.list_contacts())
        labels=re.findall(r'<option value="[^"]*">([^<]*Mira Example[^<]*)</option>',page)
        self.assertEqual(len(set(map(html.unescape,labels))),2)
