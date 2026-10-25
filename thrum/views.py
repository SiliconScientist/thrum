"""Small server-rendered views; all user-controlled values are escaped."""
from html import escape
import csv
import io


def delimited(rows, delimiter):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter, lineterminator="\n")
    writer.writerows(rows)
    return stream.getvalue().removesuffix("\n")


def e(value):
    return escape(str(value), quote=True)


def link(url, label, cls=''):
    return f'<a class="{e(cls)}" href="{e(url)}">{e(label)}</a>'


def page(title, body):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · Thrum</title>
<link rel="stylesheet" href="/style.css"></head><body>
<header><a class="brand" href="/">thrum<span class="brand-dot">●</span></a><nav aria-label="Main navigation">
<a href="/">Contacts</a><a href="/portability">Your data</a><span class="local">● Local &amp; private</span></nav></header>
<main>{body}</main><footer>Made for meaningful connections. Your data stays on this device.</footer></body></html>'''


def hidden(name, value):
    return f'<input type="hidden" name="{e(name)}" value="{e(value)}">'


def field(name, label, value='', *, multiline=False, required=False, limit=20000, help_text=''):
    attrs = f'name="{e(name)}" id="{e(name)}" maxlength="{limit}"' + (' required' if required else '')
    control = f'<textarea {attrs} rows="5">{e(value)}</textarea>' if multiline else f'<input {attrs} value="{e(value)}">'
    return f'<div class="field"><label for="{e(name)}">{e(label)}</label>{control}<small>{e(help_text)}</small></div>'


def select(name, label, options, value=''):
    choices = ''.join(f'<option value="{e(k)}"'+(' selected' if k == value else '')+f'>{e(v)}</option>' for k,v in options)
    return f'<div class="field"><label for="{e(name)}">{e(label)}</label><select name="{e(name)}" id="{e(name)}">{choices}</select></div>'


def index(contacts, query='', kind='', tag=''):
    cards = ''
    for c in contacts:
        tags = ''.join(f'<span class="tag">{e(t)}</span>' for t in c['tags'])
        subtitle = c['affiliation'] or ('Organization' if c['kind']=='organization' else 'Person')
        cards += f'<article class="card"><span class="eyebrow">{e(c["kind"])}</span><h2>{link("/contacts/"+c["id"],c["name"])}</h2><p>{e(subtitle)}</p><div class="tags">{tags}</div></article>'
    if not cards:
        cards = '<div class="empty"><h2>No contacts here yet</h2><p>Add someone you want to keep in touch with, or try a different search.</p></div>'
    return page('Contacts', f'''<div class="heading"><div><span class="eyebrow">Your circle</span><h1>Keep people close.</h1>
<p class="lede">A little context for the connections that matter.</p></div>{link('/contacts/new','+ Add contact','button')}</div>
<form class="search" method="get" action="/">{field('q','Search',query,limit=1000,help_text='Name, affiliation, contact detail, or tag')}
{select('kind','Type',[('','Everyone'),('person','People'),('organization','Organizations')],kind)}
{field('tag','Tag',tag,limit=100)}<button type="submit">Search</button>{link('/','Clear')}</form>
<p class="count">{len(contacts)} contact{'s' if len(contacts)!=1 else ''}</p><section class="cards" aria-label="Contacts">{cards}</section>''')


def contact_form(token, c=None, error='', submitted=None):
    c = c or dict(name='',kind='person',affiliation='',methods=[],tags=[],notes='')
    values = {**c, 'methods':delimited([[m['kind'],m['value'],m['label']] for m in c['methods']], '|'), 'tags':delimited([c['tags']], ',')}
    if submitted: values.update(submitted)
    editing = 'id' in c
    title = 'Edit contact' if editing else 'Add a contact'
    action = '/contacts/'+c['id']+'/edit' if editing else '/contacts/new'
    cancel = '/contacts/'+c['id'] if editing else '/'
    body = f'<div class="narrow"><span class="eyebrow">Your circle</span><h1>{title}</h1><p>Names do not need to be unique. Each contact has its own identity.</p>'
    if error: body += f'<p class="error" role="alert">{e(error)}</p>'
    body += f'<form method="post" action="{action}">{hidden("csrf",token)}'
    if editing: body += hidden('revision',c['revision'])
    body += field('name','Name',values['name'],required=True,limit=300)
    body += select('kind','Contact type',[('person','Person'),('organization','Organization')],values['kind'])
    body += field('affiliation','Organization or affiliation',values['affiliation'],limit=1000)
    body += field('methods','Contact details',values['methods'],multiline=True,help_text='One per line: type | value | optional label. Example: email | hello@example.invalid | work')
    body += field('tags','Tags',values['tags'],multiline=True,limit=20000,help_text='Separate tags with commas. Keep quotation marks around a tag that contains a comma.')
    body += field('notes','Notes',values['notes'],multiline=True)
    return page(title,body+f'<div class="actions"><button>Save contact</button>{link(cancel,"Cancel")}</div></form></div>')


def detail(c, edges, contacts):
    lookup = {v['id']:v for v in contacts}
    body = f'<div class="heading"><div><span class="eyebrow">{e(c["kind"])}</span><h1>{e(c["name"])}</h1><p class="lede">{e(c["affiliation"])}</p></div>{link("/contacts/"+c["id"]+"/edit","Edit contact","button secondary")}</div>'
    body += '<div class="detail-grid"><section class="panel"><h2>Contact details</h2>'
    for m in c['methods']:
        body += f'<p><strong>{e(m["kind"])}{(" · "+e(m["label"])) if m["label"] else ""}</strong><br>{e(m["value"])}</p>'
    if not c['methods']: body += '<p class="muted">No contact details added.</p>'
    body += '<div class="tags">'+''.join(f'<span class="tag">{e(t)}</span>' for t in c['tags'])+'</div></section>'
    body += f'<section class="panel"><h2>Notes</h2><p class="prose">{e(c["notes"]) or "No notes yet."}</p></section></div>'
    body += f'<div class="heading compact"><h2>Relationships</h2>{link("/relationships/new?source="+c["id"],"+ Add relationship","button secondary")}</div>'
    for direction, key, other in [('Outgoing','source','target'),('Incoming','target','source')]:
        body += f'<section class="panel"><h3>{direction}</h3>'
        matches = [r for r in edges if r[key] == c['id']]
        for r in matches:
            target = lookup[r[other]]
            body += f'<article class="relationship"><div><strong>{e(r["type"])}</strong> · {link("/contacts/"+target["id"],target["name"])}<p class="prose">{e(r["notes"])}</p></div><div class="actions">{link("/relationships/"+r["id"]+"/edit","Edit")}{link("/relationships/"+r["id"]+"/delete","Remove")}</div></article>'
        if not matches: body += '<p class="muted">No relationships recorded.</p>'
        body += '</section>'
    body += f'<p class="identity">Stable ID: {e(c["id"])}</p>{link("/contacts/"+c["id"]+"/delete","Delete contact","danger-link")}'
    return page(c['name'],body)


def relationship_form(token, contacts, edge=None, source='', error='', submitted=None):
    edge = edge or dict(source=source,target='',type='',notes='')
    values={**edge, **(submitted or {})}
    title='Edit relationship' if 'id' in edge else 'Add a relationship'
    options=[('', 'Choose a contact')]+[(c['id'],c['name']+' · '+(c['affiliation'] or c['kind'])+' · '+c['id']) for c in contacts]
    action='/relationships/'+edge['id']+'/edit' if 'id' in edge else '/relationships/new'
    body=f'<div class="narrow"><h1>{title}</h1><p>Direction matters: “From” has this relationship to “To”.</p>'
    if error: body += f'<p class="error" role="alert">{e(error)}</p>'
    body += f'<form method="post" action="{action}">{hidden("csrf",token)}'
    if 'id' in edge: body+=hidden('revision',edge['revision'])
    body+=select('source','From',options,values['source'])+select('target','To',options,values['target'])
    body+=field('type','Relationship type',values['type'],required=True,limit=100,help_text='For example: introduced, colleague of, member of.')
    body+=field('notes','Notes',values['notes'],multiline=True)
    return page(title,body+'<div class="actions"><button>Save relationship</button>'+link('/','Cancel')+'</div></form></div>')


def delete_form(token, item, kind):
    title = 'Delete contact' if kind=='contacts' else 'Remove relationship'
    label = item['name'] if kind=='contacts' else item['type']
    warning = 'This also removes all incoming and outgoing relationships for this contact.' if kind=='contacts' else 'The contacts themselves will be kept.'
    return page(title,f'<div class="narrow"><h1>{title}</h1><p>Remove <strong>{e(label)}</strong>?</p><p>{warning} This cannot be undone.</p><form method="post" action="/{kind}/{item["id"]}/delete">{hidden("csrf",token)}{hidden("revision",item["revision"])}<label class="confirm"><input type="checkbox" name="confirm" value="yes" required> I confirm this deletion.</label><div class="actions"><button class="danger">{title}</button>{link("/","Cancel")}</div></form></div>')


def portability():
    return page('Your data','''<div class="narrow"><span class="eyebrow">Private by design</span><h1>Your connections. Your data.</h1>
<p>Thrum stores everything in a private SQLite file on this device. There is no account, cloud sync, or external tracking.</p>
<section class="panel"><h2>Backup and export</h2><p>Use the terminal commands in the README to save a consistent database backup or a portable JSON export. Files are created outside Git checkouts and existing files are never overwritten.</p></section>
<section class="panel"><h2>Restore or import</h2><p>Import a Thrum JSON export into a new, empty database. This preserves contact and relationship IDs and avoids accidental overwrites. A database backup can also be opened directly.</p></section>
<p>Files are not encrypted by Thrum. Keep your device account secure and protect backups. A browser extension or another program running as you may be able to access local data.</p></div>''')
