# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Forms we gonna need to handle creation and editing of entries

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os

from pyClanSphere.api import *
from pyClanSphere.models import User
from pyClanSphere.utils import forms
from pyClanSphere.utils.validators import ValidationError, is_not_whitespace_only

from pyClanSphere.plugins.gamesquad.models import Squad

from pyClanSphere.plugins.war.models import War, WarMode, WarMap, WarMember, WarResult, warstates, memberstates


class _WarBoundForm(forms.Form):

    def __init__(self, war, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.war = war

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.war = self.war
        widget.new = self.war is None
        return widget


class EditWarForm(_WarBoundForm):
                 
    clanname = forms.TextField(lazy_gettext(u'Opponent'), max_length=64,
                                validators=[is_not_whitespace_only()],
                                required=True)
    date = forms.DateTimeField(lazy_gettext(u'Date'))
    server = forms.TextField(lazy_gettext(u'Server'), max_length=64)
    mode = forms.ModelField(WarMode, 'id', lazy_gettext(u'Warmode'),
                            widget=forms.SelectBox)
    playerchangecount = forms.IntegerField(lazy_gettext(u'Player Changes'), 
                      help_text=lazy_gettext(u'How many playerchanges are allowed each mapchange'))
    contact = forms.TextField(lazy_gettext(u'Opponent contact'), max_length=250,
                              validators=[is_not_whitespace_only()],
                              required=True)
    orgamember = forms.ModelField(User, 'id', lazy_gettext(u'Orgamember'),
                                  required=True, widget=forms.SelectBox)
    status = forms.ChoiceField(lazy_gettext(u'State'), required=True)
    notes = forms.TextField(lazy_gettext(u'Notes'), max_length=65000,
                           widget=forms.Textarea)
    newmap = forms.ChoiceField(lazy_gettext(u'Add map'),
                              widget=forms.SelectBox)
    removemaps = forms.MultiChoiceField(lazy_gettext(u'Check to remove'),
                                        widget=forms.CheckboxGroup)
    newmember = forms.ChoiceField(lazy_gettext(u'Add member'),
                                  widget=forms.SelectBox)
    newmemberstatus = forms.ChoiceField(lazy_gettext(u'Status for newly added member'),
                                        widget=forms.SelectBox)
    removemembers = forms.MultiChoiceField(lazy_gettext(u'Check to remove'),
                                           widget=forms.CheckboxGroup)
    
    def __init__(self, war=None, initial=None):
        if war is not None:
            initial = forms.fill_dict(initial,
                clanname = war.clanname,
                date = war.date,
                server = war.server,
                mode = war.mode,
                playerchangecount = war.playerchangecount,
                contact = war.contact,
                orgamember = war.orgamember,
                status = war.status,
                notes = war.notes
            )
        _WarBoundForm.__init__(self, war, initial)
        self.status.choices = [(k, v) for k, v in warstates.iteritems()]
        self.orgamember.choices = [(user.id, user.display_name) for user in User.query.all()]
        self.mode.choices = [(mode.id, mode.name) for mode in WarMode.query.all()]
        self.newmemberstatus.choices = [(k, v) for k, v in memberstates.iteritems()]
        if war is not None:
            self.removemembers.choices = [(member.id, '%s (%s)' % \
                                          (member.display_name, memberstates[war.memberstatus[member]]))
                                          for member in war.members]
            self.newmember.choices = [(-1, u'')] + [(member.id, member.display_name)
                                      for member in User.query.all() if member not in war.members]
            self.removemaps.choices = [(map.id, map.name) for map in war.maps]
            self.newmap.choices = [(-1, u'')] + [(map.id, map.name)
                                   for map in WarMap.query.all() if map not in war.maps]
        else:
            self.newmember.choices = [(-1, u'')] + [(member.id, member.display_name)
                                   for member in User.query.all()]
            self.newmap.choices = [(-1, u'')] + [(map.id, map.name)
                                   for map in WarMap.query.all()]
            del self.removemembers
            del self.removemaps

    def _set_common_attributes(self, war):
        forms.set_fields(war, self.data, 'clanname', 'date', 'server',
                         'mode', 'playerchangecount', 'contact', 'orgamember',
                         'status', 'notes')
        newmap_id =  self.data['newmap']
        if newmap_id != -1:
            newmap = WarMap.query.get(newmap_id)
            if newmap is not None:
                war.maps.append(newmap)
        newmember_id =  self.data['newmember']
        if newmember_id != -1:
            newmember = User.query.get(newmember_id)
            if newmember is not None:
                war.memberstatus[newmember] = self.data['newmemberstatus']
                         
    def save_changes(self):
        """Apply the changes."""
        self._set_common_attributes(self.war)
        if 'removemaps' in self.data:
            for mapid in self.data['removemaps']:
                delmap = WarMap.query.get(mapid)
                if delmap is not None:
                    self.war.maps.remove(delmap)
        if 'removemembers' in self.data:
            for memberid in self.data['removemembers']:
                member = WarMember.query.get((self.war.id,memberid))
                if member is not None:
                    db.delete(member)

    def make_war(self):
        """A helper function that creates a new user object."""
        war = War()
        self._set_common_attributes(war)
        self.war = war
        return war


class DeleteWarForm(_WarBoundForm):
    """Used to delete a war from the admin panel."""

    def delete_war(self):
        """Deletes the war"""
        for warmap in self.war.maps:
            db.delete(warmap)
        for member in self.war.members:
            db.delete(member)
        if self.war.result:
            db.delete(self.war.result)
        db.delete(self.war)


class _WarMapBoundForm(forms.Form):
    """Base class for WarMap related forms"""
    def __init__(self, warmap, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.warmap = warmap

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.warmap = self.warmap
        widget.new = self.warmap is None
        return widget


class EditWarMapForm(_WarMapBoundForm):
                 
    mapname = forms.TextField(lazy_gettext(u'Internal Mapname'), max_length=64,
                            validators=[is_not_whitespace_only()],
                            required=True)
    squad = forms.ChoiceField(lazy_gettext(u'Owning squad'),
                              widget=forms.SelectBox)
    readmapname = forms.BooleanField(lazy_gettext(u'Use name from file metadata as internal mapname'),
                      help_text=lazy_gettext(u'Read map metadata and set internal mapname to name from mapfile'))
    
    def __init__(self, warmap=None, initial=None):
        if warmap is not None:
            initial = forms.fill_dict(initial,
                mapname = warmap.name,
                squad = warmap.squad
            )
        _WarMapBoundForm.__init__(self, warmap, initial)
        self.squad.choices = [('','')] + [(squad.id, squad.name) for squad in Squad.query.all()]

    def _set_common_attributes(self, warmap):
        warmap.name = self.data['mapname']
        warmap.squad = Squad.query.get(self.data['squad'])
        #forms.set_fields(warmap, self.data,'name')
                         
    def save_changes(self):
        """Apply the changes."""
        self._set_common_attributes(self.warmap)

    def make_warmap(self):
        """A helper function that creates a new user object."""
        warmap = WarMap()
        self._set_common_attributes(warmap)
        self.warmap = warmap
        return warmap

    @property
    def overwrite_mapname(self):
        return self.data['readmapname']

class DeleteWarMapForm(_WarMapBoundForm):
    """Used to delete a warmap from the admin panel."""

    def delete_warmap(self):
        """Deletes the warmap‚"""
        self.warmap.remove_file()
        db.delete(self.warmap)

class EditWarResultForm(forms.Form):

    our_points = forms.IntegerField(lazy_gettext(u'Our Points'))
    enemy_points = forms.IntegerField(lazy_gettext(u'Enemy Points'))
    comment = forms.TextField(lazy_gettext(u'Comment'), max_length=65000,
                              widget=forms.Textarea)
    status = forms.ChoiceField(lazy_gettext(u'State'), required=True)

    def __init__(self, war, warresult=None, initial=None):
        if warresult is not None:
            initial = forms.fill_dict(initial,
                our_points = warresult.our_points,
                enemy_points = warresult.enemy_points,
                comment = warresult.comment
            )
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.warresult = warresult
        self.war = war
        self.status.choices = [(k, v) for k, v in warstates.iteritems()]

    def _set_common_attributes(self, warresult):
        forms.set_fields(warresult, self.data, 'our_points', 'enemy_points', 'comment')
        self.war.status = self.data['status']

    def save_changes(self):
        """Apply the changes."""
        self._set_common_attributes(self.warresult)

    def make_warresult(self):
        """A helper function that creates a new user object."""
        warresult = WarResult(self.war)
        self._set_common_attributes(warresult)
        self.warresult = warresult
        return warresult

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.warresult = self.warresult
        widget.war = self.war
        widget.new = self.war is None
        return widget

