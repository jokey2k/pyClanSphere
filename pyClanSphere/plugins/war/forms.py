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

from pyClanSphere.plugins.war.models import War, WarMode, WarMap, warstates


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
    date = forms.DateField(lazy_gettext(u'Date'))
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
        if war is not None:
            self.removemaps.choices = [(map.id, map.name) for map in war.maps]
            self.newmap.choices = [(-1, u'')] + [(map.id, map.name)
                                   for map in WarMap.query.all() if map not in war.maps]
        else:
            self.newmap.choices = [(-1, u'')] + [(map.id, map.name)
                                   for map in WarMap.query.all()]
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
                         
    def save_changes(self):
        """Apply the changes."""
        self._set_common_attributes(self.war)
        if 'removemaps' in self.data:
            for mapid in self.data['removemaps']:
                delmap = WarMap.query.get(mapid)
                if delmap is not None:
                    self.war.maps.remove(delmap)

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
        self.war.maps.clear()
        self.war.members.clear()
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


class DeleteWarMapForm(_WarMapBoundForm):
    """Used to delete a warmap from the admin panel."""

    def delete_warmap(self):
        """Deletes the warmap‚"""
        self.warmap.remove_map_file()
        db.delete(self.warmap)