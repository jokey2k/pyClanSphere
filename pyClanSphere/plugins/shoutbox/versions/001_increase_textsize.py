"""increase textsize"""
# Keep __doc__ to a single line
from pyClanSphere.upgrades.versions import *

# use this or define your own if you need
metadata = db.MetaData()

# Define tables here
shoutboxentries = db.Table('shoutboxentries', metadata,
    db.Column('entry_id', db.Integer, primary_key=True),
    db.Column('author', db.String(50)),
    db.Column('user_id', db.ForeignKey('users.user_id')),
    db.Column('existing_user', db.Boolean),
    db.Column('ip', db.String(64)),
    db.Column('postdate', db.DateTime),
    db.Column('text', db.String(255))
)
# Define the objects here


def map_tables(mapper):
    clear_mappers()
    # Map tables to the python objects here


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine
    # bind migrate_engine to your metadata
    session = scoped_session(lambda: create_session(migrate_engine,
                                                    autoflush=True,
                                                    autocommit=False))
    map_tables(session.mapper)
    metadata.bind = migrate_engine
    yield u'<p>Increasing space for shoutbox texts</p>'
    shoutboxentries.c.text.alter(type=db.Text)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    session = scoped_session(lambda: create_session(migrate_engine,
                                                    autoflush=True,
                                                    autocommit=False))
    map_tables(session.mapper)
    metadata.bind = migrate_engine
    yield u'<p>Decreasing space for shoutbox texts</p>'
    shoutboxentries.c.text.alter(type=db.String(255))

