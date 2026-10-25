"""Invented examples written for this project; never derived from a contact store."""
from .portability import import_data


def seed(store):
    ids=['00000000-0000-4000-8000-00000000000'+str(n) for n in range(1,8)]
    def contact(i,name,kind,affiliation,tags,notes):
        return dict(id=ids[i],name=name,kind=kind,affiliation=affiliation,tags=tags,notes=notes,
                    methods=[],revision=1)
    contacts=[
        contact(0,'Mira Chen','person','Lantern Workshop',['bikes','volunteer'],
                'Met at the library repair café. Offered to teach bicycle puncture repairs; ask about bringing spare inner tubes.'),
        contact(1,'Rowan Ellis','person','Maple Library',['organizer','volunteer'],
                'Coordinates the repair café and introduced me to Mira. Confirm table space and accessible entrances before the next session.'),
        contact(2,'Lantern Workshop','organization','',['tools','repair'],
                'Community workshop lending repair stands and hand tools. Mira is the contact for borrowing bicycle equipment.'),
        contact(3,'Samira Patel','person','Willow Neighbors',['sewing','volunteer'],
                'Brings a sewing machine and teaches simple clothing repairs. Prefers email; available for afternoon sessions.'),
        contact(4,'Theo Brooks','person','Lantern Workshop',['electronics','volunteer'],
                'Mira introduced us at a workshop open day. Can help diagnose battery-powered toys; ask for a list of supplies.'),
        contact(5,'Maple Library','organization','',['venue','community'],
                'Hosts the neighborhood repair café in its meeting room. Rowan coordinates room bookings and volunteer tables.'),
        contact(6,'Willow Neighbors','organization','',['community','outreach'],
                'Neighborhood group helping people find the repair café. Samira organizes flyers and recruits sewing volunteers.'),
    ]
    for i,local in [(0,'mira'),(1,'rowan'),(3,'samira'),(4,'theo')]:
        contacts[i]['methods']=[dict(kind='email',value=f'{local}@example.invalid',label='personal')]
    contacts[0]['methods'].append(dict(kind='email',value='mira-workshop@example.invalid',label='workshop equipment'))
    contacts[5]['methods']=[dict(kind='email',value='library-bookings@example.invalid',label='room bookings')]
    relationships=[]
    edges=[
        (1,0,'introduced','Rowan introduced me to Mira while planning the bicycle repair table.'),
        (0,4,'introduced','Mira connected me with Theo for help repairing battery-powered toys.'),
        (0,2,'member of','Coordinates borrowing bicycle tools for the repair café.'),
        (4,2,'member of','Helps run the electronics repair bench.'),
        (1,5,'works at','Coordinates the meeting room and repair café schedule.'),
        (0,5,'volunteers with','Teaches bicycle puncture repairs at the repair café.'),
        (3,6,'member of','Organizes neighborhood outreach and sewing volunteers.'),
        (3,5,'volunteers with','Hosts the clothing repair table during afternoon sessions.'),
        (6,5,'partners with','Shares repair café flyers and recruits volunteers.'),
    ]
    for i,(source,target,kind,notes) in enumerate(edges,1):
        relationships.append(dict(id='00000000-0000-4000-9000-00000000000'+str(i),source=ids[source],target=ids[target],type=kind,notes=notes,revision=1))
    import_data(store,dict(format='thrum',version=1,contacts=contacts,relationships=relationships))
