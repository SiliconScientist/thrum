"""Invented examples written for this project; never derived from a contact store."""
from .portability import import_data


def seed(store):
    ids=['00000000-0000-4000-8000-00000000000'+str(n) for n in range(1,5)]
    def contact(i,name,kind,affiliation,tags,notes):
        return dict(id=ids[i],name=name,kind=kind,affiliation=affiliation,tags=tags,notes=notes,
                    methods=[],revision=1)
    contacts=[
        contact(0,'Mira Example','person','Lantern Workshop',['friend','making'], 'Fictional demo contact. Enjoys inventing tiny paper cities.'),
        contact(1,'Rowan Sample','person','Cloudberry Reading Circle',['books'], 'Fictional demo contact. Helps organize imaginary reading evenings.'),
        contact(2,'Lantern Workshop','organization','',['community','making'], 'Fictional organization used to demonstrate membership.'),
        contact(3,'Mira Example','person','Imaginary Observatory',['science'], 'A second fictional person with the same name and a different stable ID.'),
    ]
    contacts[0]['methods']=[dict(kind='email',value='mira@example.invalid',label='demo')]
    contacts[1]['methods']=[dict(kind='email',value='rowan@example.invalid',label='demo')]
    relationships=[]
    for i,(source,target,kind) in enumerate([(0,1,'introduced'),(0,2,'member of'),(1,2,'volunteers with')],1):
        relationships.append(dict(id='00000000-0000-4000-9000-00000000000'+str(i),source=ids[source],target=ids[target],type=kind,notes='Entirely fictional demonstration relationship.',revision=1))
    import_data(store,dict(format='thrum',version=1,contacts=contacts,relationships=relationships))
