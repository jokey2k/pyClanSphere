# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.war_module
    ~~~~~~~~~~~~~~~~~~~~~~~

    Plugin implementation description goes here.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os
from datetime import datetime

from werkzeug import FileStorage

from pyClanSphere.api import db, _
from pyClanSphere.models import User
from pyClanSphere.utils.pagination import Pagination

from pyClanSphere.plugins.gamesquad.models import Game, Squad
from pyClanSphere.plugins.war.database import wars, war_maps, warmembers, \
     warmodes, warmaps, warresults, warmap_results

try:
    import cPickle as Pickle
except:
    import Pickle

warstates = {
    1:_('Incomplete'),
    2:_('Planned'),
    3:_('Running'),
    4:_('Finished'),
    5:_('Aborted'),
    6:_('Cancelled')
}

memberstates = {
    1:_('No'),
    2:_('Maybe'),
    3:_('Yes')
}

def _create_warmember(member, status):
    """A creator function for creating warmembers from member and status info"""
    return WarMember(member=member, status=status)


class WarMetaQuery(db.Query):
    """Meta-Addon methods for querying on war-related classes"""

    def get_list(self, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True, paginator=Pagination):
        """Return a dict with pagination and wars."""

        if per_page is None:
            per_page = 20

        # send the query
        offset = per_page * (page - 1)
        mylist = self.offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not mylist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args)

        return {
            'datalist':         mylist,
            'pagination':       pagination
        }


class WarQuery(db.Query):
    """Addon methods for querying wars"""

    def upcoming(self):
        """Return a filter for upcoming wars only"""

        return self.filter_by(status=2)
        
    def past(self):
        """Return a filter for past played wars only"""
        
        return self.filter_by(status=4)

    def get_list(self, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True, paginator=Pagination):
        """Return a dict with pagination and wars."""

        if per_page is None:
            per_page = 20

        # send the query
        offset = per_page * (page - 1)
        warlist = self.order_by(db.desc(War.date)) \
                         .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not warlist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args)

        return {
            'wars':             warlist,
            'pagination':       pagination,
            'warstates':        warstates
        }
        

class War(object):
    """One Coordinated war"""

    memberstatus = db.association_proxy('by_member', 'status', creator=_create_warmember)
    query = db.query_property(WarQuery)

    def __init__(self, clanname=u'', date=None, server=None, mode=None,
                 members=None, maps=None, playerchangecount=0,
                 contact=None, orgamember=None, checked=False, status=1,
                 notes=None, result=None, squad=None):
        super(War, self).__init__()
        self.clanname = clanname
        self.date = date
        self.server = server
        self.squad = squad
        self.mode = mode
        self.playerchangecount = playerchangecount
        self.contact = contact
        self.orgamember = orgamember
        self.checked = checked
        self.status = status
        self.result = result
        self.notes = notes

    def can_create(self, user=None):
        return True

    def can_edit(self, user=None):
        return True

    def __repr__(self):
        return "<%s (%s, %s)>" % (
            self.__class__.__name__,
            self.clanname,
            self.date
        )


class WarMember(object):
    """Memberstatus for a war"""
    
    def __init__(self, war=None, member=None, status=1):
        self.war = war
        self.member = member
        self.status = status


class WarMode(object):
    """Pre-defined war modes, has free fields for game-dependent infos"""

    query = db.query_property(WarMetaQuery)

    def __init__(self, name=u'', game=None, free1=None, free2=None, free3=None, remotedata=None):
        self.name = name
        self.game = game
        self.free1 = free1
        self.free2 = free2
        self.free3 = free3

        # This is used for serversettings, do not touch otherwise!
        self.remotedata = remotedata

    def can_create(self, user=None):
        return True

    def can_edit(self, user=None):
        return True


class WarMap(object):
    """A war map"""

    query = db.query_property(WarMetaQuery)
    
    def __init__(self, name=u'', squad=None, metadata_timestamp=None, metadata_cache=None):
        self.name = name
        self.squad = squad
        self.metadata_timestamp = metadata_timestamp
        self.metadata_cache = metadata_cache
    
    def generate_filename(self):   
        from pyClanSphere.api import get_application
        app = get_application()
        self.map_folder = os.path.join(app.instance_folder, 'warmaps')
        self._map_filename = os.path.join(self.map_folder, str(self.id))

    def can_create(self, user=None):
        return True

    def can_edit(self, user=None):
        return True

    @property
    def map_filename(self):
        try:
            return self._map_filename
        except AttributeError:
            self.generate_filename()
            return self._map_filename

    @property
    def metadata(self):
        """Return map metadata"""
        
        if not self.has_file():
            return None

        statinfo = os.stat(self.map_filename)
        filetime = datetime.fromtimestamp(statinfo.st_mtime)
        if self.metadata_timestamp and filetime <= self.metadata_timestamp:
            return Pickle.loads(self.metadata_cache)
        else:
            have_metadata = False

            # more filetypes can be added later, just using this for now but prepared it
            from pyClanSphere._ext.GBXChallengeReader import GBXChallengeReader, GBXWrongFileTypeException
            try:
                data = GBXChallengeReader(self.map_filename)
                have_metadata = True
            except GBXWrongFileTypeException:
                pass
            
            if have_metadata:
                self.metadata_cache = Pickle.dumps(data)
                self.metadata_timestamp = filetime
                return data

            return None
            
    def place_file(self, newfile):
        """Move war map file to instance subfolder and generate appropriate filename"""

        if isinstance(newfile, FileStorage):
            newfile.save(self.map_filename)
        else:
            raise NotImplemented('Dunno how to handle that kind of file object')

    def remove_file(self):
        """Remove a war map file"""
        
        if os.path.exists(self.map_filename):
            os.remove(self.map_filename)
    
    def has_file(self):
        """True/False if we have something"""
        
        return os.path.exists(self.map_filename)
    

class WarResult(object):
    """Details on the result"""
    
    def __init__(self, war, our_points=0, enemy_points=0):
        self.id = war.id
        self.our_points = our_points
        self.enemy_points = enemy_points

    @property
    def points(self):
        return "%s:%s" % (self.our_points, self.enemy_points)


class NullWarResult(WarResult):
    """Empty War Result"""

    points = "--:--"
    def __init__(self):
        self.id = -1


class NullWar(War):
    """Fake War so display routines will work flawless if there
       are not enough wars yet
    """
    id = -1
    clanname = "--"
    server = "--"        
    date = None
    result = NullWarResult()


# Lazy people :D
mapper=db.mapper
relation=db.relation
backref=db.backref

mapper(War, wars, properties={
    'id':               wars.c.war_id,
    'by_member':        relation(WarMember,
                        collection_class=db.attribute_mapped_collection('member')),
    'maps':             relation(WarMap, secondary=war_maps),
    'squad':            relation(Squad, uselist=False,
                                 backref=backref('wars')),
    'members':          relation(User, secondary=warmembers),
    'orgamember':       relation(User, uselist=False),
    'mode':             relation(WarMode, uselist=False)
})
mapper(WarMember, warmembers, properties={
    'war':              relation(War),
    'member':           relation(User)
})
mapper(WarMode, warmodes, properties={
    'id':               warmodes.c.warmode_id,
    'game':             relation(Game, uselist=False)
})
mapper(WarMap, warmaps, properties={
    'id':               warmaps.c.map_id,
    'squad':            relation(Squad, uselist=False,
                                 backref=backref('warmaps'))
})
mapper(WarResult, warresults, properties={
    'id':               warresults.c.war_id,
    'war':              relation(War, uselist=False, backref=backref('result', uselist=False)),
    'maps':             relation(WarMap, secondary=warmap_results)
})