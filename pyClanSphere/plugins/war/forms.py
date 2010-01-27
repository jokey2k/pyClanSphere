# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.war.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Forms we gonna need to handle creation and editing of entries

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os

from pyClanSphere.api import *
from pyClanSphere.models import User
from pyClanSphere.utils import forms
from pyClanSphere.utils.validators import ValidationError, is_not_whitespace_only, is_valid_url, is_valid_email

from pyClanSphere.plugins.gamesquad.models import Game, Squad

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


class FightUsForm(_WarBoundForm):

    clanname = forms.TextField(lazy_gettext(u'Clan'), max_length=64,
                                validators=[is_not_whitespace_only()],
                                required=True)
    clanhomepage = forms.TextField(lazy_gettext(u'Homepage'), max_length=128,
                                   validators=[is_valid_url()])
    date = forms.DateTimeField(lazy_gettext(u'Date'), required=True)
    mode = forms.ModelField(WarMode, 'id', lazy_gettext(u'Warmode'),
                            widget=forms.SelectBox)
    squad = forms.ModelField(Squad, 'id', lazy_gettext(u'Squad'),
                             widget=forms.SelectBox, required=True)
    playerchangecount = forms.IntegerField(lazy_gettext(u'Playerchanges/map'),
                      help_text=lazy_gettext(u'How many playerchanges are allowed each mapchange'))
    contact = forms.TextField(lazy_gettext(u'Email'), max_length=250,
                              validators=[is_valid_email()],
                              required=True)
    server = forms.TextField(lazy_gettext(u'Server'), max_length=64)
    notes = forms.TextField(lazy_gettext(u'Notes'), max_length=65000,
                            widget=forms.Textarea)

    def __init__(self, war=None, initial=None):
        if war is not None:
            initial = forms.fill_dict(initial,
                clanname = war.clanname,
                clanhomepage = war.clanhomepage,
                date = war.date,
                server = war.server,
                squad = war.squad,
                mode = war.mode,
                playerchangecount = war.playerchangecount,
                contact = war.contact,
                notes = war.notes
            )
        _WarBoundForm.__init__(self, war, initial)
        self.mode.choices = [(mode.id, mode.name) for mode in WarMode.query.all()]
        self.squad.choices = [(squad.id, '%s (%s)' % (squad.name, squad.game.name)) for squad in Squad.query.all()]

    @property
    def captcha_protected(self):
        """We're protected if no user is logged in and config says so."""
        return not self.request.user.is_somebody and self.app.cfg['recaptcha_enable']

    def make_war(self):
        """A helper function that creates a new user object."""
        war = War()
        self._set_common_attributes(war)
        self.war = war
        #hardcoded fightus, user doesn't need to set it
        self.war.status=0
        return war

    def _set_common_attributes(self, war):
        forms.set_fields(war, self.data, 'clanname', 'date', 'server',
                         'mode', 'playerchangecount', 'contact',
                         'notes', 'squad', 'clanhomepage')

    def save_changes(self):
        """Apply the changes."""
        self._set_common_attributes(self.war)

        # this is a fightus request, so force status=0
        self.war.status = 0


class EditWarForm(FightUsForm):

    orgamember = forms.ModelField(User, 'id', lazy_gettext(u'Orgamember'),
                                  required=True, widget=forms.SelectBox)
    status = forms.ChoiceField(lazy_gettext(u'State'), required=True)
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
                orgamember = war.orgamember,
                status = war.status
            )
        FightUsForm.__init__(self, war, initial)
        self.contact.required = False
        self.status.choices = [(k, v) for k, v in warstates.iteritems()]
        self.orgamember.choices = [(user.id, user.display_name) for user in User.query.namesort().all()]
        self.newmemberstatus.choices = [(k, v) for k, v in memberstates.iteritems()]
        if war is not None:
            self.removemembers.choices = [(member.id, '%s (%s)' % \
                                          (member.display_name, memberstates[war.memberstatus[member]]))
                                          for member in war.members]
            self.newmember.choices = [(-1, u'')] + [(member.id, member.display_name)
                                      for member in User.query.namesort().all() if member not in war.members]
            self.removemaps.choices = [(map.id, map.name) for map in war.maps]
            self.newmap.choices = [(-1, u'')] + [(map.id, map.name)
                                   for map in WarMap.query.all() if map not in war.maps]
        else:
            self.newmember.choices = [(-1, u'')] + [(member.id, member.display_name)
                                   for member in User.query.namesort().all()]
            self.newmap.choices = [(-1, u'')] + [(map.id, map.name)
                                   for map in WarMap.query.all()]
            del self.removemembers
            del self.removemaps

    def _set_common_attributes(self, war):
        FightUsForm._set_common_attributes(self, war)
        forms.set_fields(war, self.data, 'orgamember', 'status')
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
                squad = warmap.squad.id if warmap.squad else None,
                readmapname = 1
            )
        else:
            initial = forms.fill_dict(initial,
                mapname = _('MapName'),
                readmapname = 1
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

    our_points = forms.IntegerField(lazy_gettext(u'Our Points'), required=True)
    enemy_points = forms.IntegerField(lazy_gettext(u'Enemy Points'), required=True)
    comment = forms.TextField(lazy_gettext(u'Comment'), max_length=65000,
                              widget=forms.Textarea)
    status = forms.ChoiceField(lazy_gettext(u'State'), required=True)

    def __init__(self, war, warresult=None, initial=None):
        if warresult is not None:
            initial = forms.fill_dict(initial,
                our_points = warresult.our_points,
                enemy_points = warresult.enemy_points,
                comment = warresult.comment,
                status = war.status
            )
        else:
            initial = forms.fill_dict(initial,
                status = war.status if war.status > 3 else 4
            )
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.warresult = warresult
        self.war = war
        self.status.choices = [(k, v) for k, v in warstates.iteritems() if k > 3]

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

class _WarModeBoundForm(forms.Form):
    """Base class for WarMode related forms"""
    def __init__(self, warmode, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.warmode = warmode

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.warmode = self.warmode
        widget.new = self.warmode is None
        return widget


class EditWarModeForm(_WarModeBoundForm):

    modename = forms.TextField(lazy_gettext(u'Modename'), max_length=64,
                            validators=[is_not_whitespace_only()],
                            required=True)
    game = forms.ChoiceField(lazy_gettext(u'Game'), widget=forms.SelectBox,
                             required=True)
    free1 = forms.TextField(lazy_gettext(u'Free field 1'), max_length=128)
    free2 = forms.TextField(lazy_gettext(u'Free field 2'), max_length=128)
    free3 = forms.TextField(lazy_gettext(u'Free field 3'), max_length=128)

    def __init__(self, warmode=None, initial=None):
        if warmode is not None:
            initial = forms.fill_dict(initial,
                modename = warmode.name,
                game = warmode.game.id,
                free1 = warmode.free1,
                free2 = warmode.free2,
                free3 = warmode.free3
            )
        _WarModeBoundForm.__init__(self, warmode, initial)
        self.game.choices = [(game.id, game.name) for game in Game.query.all()]

    def _set_common_attributes(self, warmode):
        forms.set_fields(warmode, self.data, 'free1', 'free2', 'free3')
        warmode.name = self.data['modename']
        warmode.game = Game.query.get(self.data['game'])

    def save_changes(self):
        """Apply the changes."""
        self._set_common_attributes(self.warmode)

    def make_warmode(self):
        """A helper function that creates a new user object."""
        warmode = WarMode()
        self._set_common_attributes(warmode)
        self.warmode = warmode
        return warmode


class DeleteWarModeForm(_WarModeBoundForm):
    """Used to delete a warmode from the admin panel."""

    def delete_warmode(self):
        """Deletes the warmode‚"""
        db.delete(self.warmode)

