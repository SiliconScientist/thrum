"""Loopback-only HTTP UI, intended for one trusted device account."""
from contextlib import closing
import csv
import io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import secrets
import sqlite3
from urllib.parse import parse_qsl, urlsplit
from .storage import Store
from . import views

MAX_BODY = 262144


def parse_pairs(value):
    if re.search(r'%(?![a-fA-F0-9]{2})', value): raise ValueError('Malformed form encoding.')
    pairs = parse_qsl(value, keep_blank_values=True, encoding='utf-8', errors='strict', max_num_fields=30)
    if len(dict(pairs)) != len(pairs): raise ValueError('Duplicate fields are not supported.')
    return dict(pairs)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        # Do not put request data or local file paths into stderr.
        pass


class Handler(BaseHTTPRequestHandler):
    server_version = 'Thrum'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass

    def send(self, code, body='', content_type='text/html; charset=utf-8', location=None):
        data = body.encode('utf-8') if isinstance(body,str) else body
        self.send_response(code)
        headers = {'Content-Type':content_type,'Content-Length':str(len(data)),
            'Cache-Control':'no-store','Referrer-Policy':'same-origin',
            'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY',
            'Content-Security-Policy':"default-src 'none'; style-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"}
        if location: headers['Location'] = location
        for k,v in headers.items(): self.send_header(k,v)
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)

    def send_error(self, code, message=None, explain=None):
        self.send(code, views.page('Request unavailable','<h1>Request unavailable</h1><p>Return to Contacts and try again.</p>'))

    def allowed(self, write=False):
        hosts=self.headers.get_all('Host',[])
        if len(hosts)!=1 or hosts[0] not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}: return False
        origins=self.headers.get_all('Origin',[])
        if write and origins != ['http://'+hosts[0]]: return False
        if origins and origins != ['http://'+hosts[0]]: return False
        return self.headers.get('Sec-Fetch-Site') != 'cross-site'

    def do_GET(self):
        if not self.allowed(): self.send_error(403); return
        try:
            target=urlsplit(self.path)
            if target.scheme or target.netloc or target.fragment: raise ValueError('Invalid URL.')
            if len(self.path)>8192: raise ValueError('URL too long.')
            params=parse_pairs(target.query)
            path=target.path
            if path=='/style.css':
                self.send(200,Path(__file__).with_name('style.css').read_bytes(),'text/css; charset=utf-8');return
            if path=='/portability': self.send(200,views.portability());return
            with closing(Store(self.server.db_path)) as store:
                store.con.execute('BEGIN')
                token=self.server.csrf
                if path=='/':
                    if set(params)-{'q','kind','tag'}: raise ValueError('Unknown filter.')
                    q,kind,tag=(params.get(k,'') for k in ('q','kind','tag'))
                    body=views.index(store.list_contacts(q,kind,tag),q,kind,tag)
                elif path=='/contacts/new': body=views.contact_form(token)
                elif path=='/relationships/new': body=views.relationship_form(token,store.list_contacts(),source=params.get('source',''))
                else:
                    match=re.fullmatch(r'/(contacts|relationships)/([a-f0-9-]{36})(?:/(edit|delete))?',path)
                    if not match: raise KeyError()
                    kind,identifier,action=match.groups()
                    item=store.get_contact(identifier) if kind=='contacts' else store.get_relationship(identifier)
                    if action=='delete': body=views.delete_form(token,item,kind)
                    elif kind=='contacts' and action=='edit': body=views.contact_form(token,item)
                    elif kind=='relationships' and action=='edit': body=views.relationship_form(token,store.list_contacts(),item)
                    elif kind=='contacts': body=views.detail(item,store.relationships(identifier),store.list_contacts())
                    else: raise KeyError()
            self.send(200,body)
        except KeyError: self.send_error(404)
        except (ValueError,UnicodeError): self.send_error(400)
        except (sqlite3.Error,OSError): self.send_error(503)

    def do_POST(self):
        if not self.allowed(write=True): self.send_error(403);return
        try:
            match=re.fullmatch(r'/(contacts|relationships)/(new|[a-f0-9-]{36}/(?:edit|delete))',self.path)
            if not match: raise KeyError()
            lengths=self.headers.get_all('Content-Length',[])
            if len(lengths)!=1 or not lengths[0].isdigit() or not 0<int(lengths[0])<=MAX_BODY: raise ValueError('Invalid body length.')
            if self.headers.get_all('Transfer-Encoding') or len(self.headers.get_all('Content-Type',[]))!=1 or self.headers.get_content_type()!='application/x-www-form-urlencoded': raise ValueError('Unsupported form encoding.')
            raw=self.rfile.read(int(lengths[0]))
            if len(raw)!=int(lengths[0]): raise ValueError('Incomplete form.')
            values=parse_pairs(raw.decode('utf-8'))
            token=values.pop('csrf','')
            if not secrets.compare_digest(token.encode(),self.server.csrf.encode()): self.send_error(403);return
            kind,rest=match.groups()
            identifier=None if rest=='new' else rest.split('/')[0]
            action='new' if rest=='new' else rest.split('/')[1]
            if action!='new':
                values['revision']=int(values['revision'])
                if values['revision']<1: raise ValueError('Invalid revision.')
            with closing(Store(self.server.db_path)) as store:
                if action=='delete':
                    if values.get('confirm')!='yes': raise ValueError('Confirm deletion first.')
                    if set(values)-{'revision','confirm'}: raise ValueError('Unknown fields.')
                    if kind=='contacts': store.delete_contact(identifier,values['revision'])
                    else: store.delete_relationship(identifier,values['revision'])
                    destination='/'
                elif kind=='contacts':
                    if set(values)-{'name','kind','affiliation','methods','tags','notes','revision'}: raise ValueError('Unknown contact fields.')
                    data=dict(values)
                    tag_rows=list(csv.reader(io.StringIO(values.get('tags',''), newline=''), strict=True, skipinitialspace=True))
                    if len(tag_rows)>1: raise ValueError('Tags must be one comma-separated row; quote embedded newlines.')
                    data['tags']=[v.strip() for v in (tag_rows[0] if tag_rows else []) if v.strip()]
                    data['methods']=[]
                    for row in csv.reader(io.StringIO(values.get('methods',''), newline=''), delimiter='|', strict=True, skipinitialspace=True):
                        if not row: continue
                        parts=[p.strip() for p in row]
                        if len(parts) not in (2,3): raise ValueError('Use type | value | optional label for each contact detail.')
                        data['methods'].append(dict(kind=parts[0],value=parts[1],label=parts[2] if len(parts)==3 else ''))
                    item=store.save_contact(data,identifier);destination='/contacts/'+item['id']
                else:
                    if set(values)-{'source','target','type','notes','revision'}: raise ValueError('Unknown relationship fields.')
                    item=store.save_relationship(values,identifier);destination='/contacts/'+item['source']
            self.send(303,location=destination)
        except KeyError: self.send_error(400)
        except (ValueError,UnicodeError,csv.Error):
            # Keep the browser's form history; never echo arbitrary exception text.
            self.send(400,views.page('Could not save','<div class="narrow"><h1>Could not save</h1><p>Check required fields, contact details, and confirmation. If this record changed in another tab, reopen it before saving. Use your browser’s Back button to recover your entries.</p>'+views.link('/','Return to contacts')+'</div>'))
        except (sqlite3.Error,OSError): self.send_error(503)


def create_server(path, port=8765):
    with closing(Store(path)) as store: db_path=store.path
    server=Server(('127.0.0.1',port),Handler)
    server.db_path=db_path
    server.csrf=secrets.token_urlsafe(32)
    return server
