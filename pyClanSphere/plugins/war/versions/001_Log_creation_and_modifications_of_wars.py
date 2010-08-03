"""Log creation and modifications of wars"""
# Keep __doc__ to a single line
from pyClanSphere.upgrades.versions import *
from pyClanSphere.schema import users
from datetime import datetime

# use this or define your own if you need
metadata = db.MetaData()

for var in ['Table', 'Column', 'DateTime', 'String', 'Integer', 'ForeignKey', 'Text', 'DateTime']:
    globals()[var] = getattr(db,var)

# Define tables here
wars = Table('wars', metadata,
    Column('war_id', Integer, primary_key=True),
    Column('clanname', String(64)),
    Column('clantag', String(16)),
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
col_c = Column('creationdate', DateTime,
               default=datetime.utcnow())
col_m = Column('modificationdate', DateTime,
               default=datetime.utcnow())
col_u = Column('modificationuser_id', Integer, ForeignKey(users.c.user_id))


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
    if not wars.exists():
        wars.create(migrate_engine)
    yield u'<p>Add creationdate column to wars</p>\n'
    col_c.create(wars, populate_default=True)
    yield u'<p>Add modificationdate column to wars</p>\n'
    col_m.create(wars, populate_default=True)
    yield u'<p>Add modificationuser column to wars</p>\n'
    col_u.create(wars, populate_default=True)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    session = scoped_session(lambda: create_session(migrate_engine,
                                                    autoflush=True,
                                                    autocommit=False))
    map_tables(session.mapper)
    metadata.bind = migrate_engine
    yield u'<p>Drop modificationuser column to wars</p>\n'
    drop_column(col_u, wars)
    yield u'<p>Drop modificationdate column from wars</p>\n'
    drop_column(col_m, wars)
    yield u'<p>Drop creationdate column from wars</p>\n'
    drop_column(col_c, wars)
