# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.war.database
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Our needed tables are declared here

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from datetime import date

from pyClanSphere.database import db, metadata

# Mapping these out from db module to increases readability further down
# As this module is only part-imported by the models and init module, it should be safe to do so
for var in ['Table', 'Column', 'String', 'Integer', 'Boolean', 'DateTime', 'ForeignKey', 'Text']:
    globals()[var] = getattr(db,var)

wars = Table('wars', metadata,
    Column('war_id', Integer, primary_key=True),
    Column('clanname', String(64)),
    Column('clanhomepage', String(128)),
    Column('date', DateTime),
    Column('server', String(64)),
    Column('warmode_id', ForeignKey('warmodes.warmode_id')),
    Column('playerchangecount', Integer),
    Column('contact', String(250)),
    Column('orgamember_id', ForeignKey('users.user_id')),
    Column('squad_id', ForeignKey('squads.squad_id')),
    Column('checked', String(250)),
    Column('status', Integer),
    Column('notes', Text)
)

warmembers = Table('warmembers', metadata,
    Column('war_id', ForeignKey('wars.war_id'), primary_key=True),
    Column('user_id', ForeignKey('users.user_id'), primary_key=True),
    Column('status', Integer)
)

war_maps = Table('war_maps', metadata,
    Column('war_id', ForeignKey('wars.war_id'), primary_key=True),
    Column('map_id', ForeignKey('warmaps.map_id'), primary_key=True)
)

warmodes = Table('warmodes', metadata,
    Column('warmode_id', Integer, primary_key=True),
    Column('name', String(64)),
    Column('game_id', ForeignKey('games.game_id')),
    Column('free1', String(128)),
    Column('free2', String(128)),
    Column('free3', String(128)),
    Column('remotedata', Text)
)

warmaps = Table('warmaps', metadata,
    Column('map_id', Integer, primary_key=True),
    Column('name', String(64)),
    Column('squad_id', ForeignKey('squads.squad_id')),
    Column('metadata_timestamp', DateTime),
    Column('metadata_cache', Text)
)

warmap_results = Table('warmap_results', metadata,
    Column('war_id', ForeignKey('warresults.war_id'), primary_key=True),
    Column('map_id', ForeignKey('warmaps.map_id'), primary_key=True),
    Column('our_points', Integer),
    Column('enemy_points', Integer),
    Column('comment', String(128))
)

warresults = Table('warresults', metadata,
    Column('war_id', ForeignKey('wars.war_id'), primary_key=True),
    Column('our_points', Integer),
    Column('enemy_points', Integer),
    Column('comment', Text)
)

def init_database(app):
    """ This is for inserting our new table"""
    engine = app.database_engine
    metadata.create_all(engine)
