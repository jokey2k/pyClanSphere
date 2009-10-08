# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.shoutbox
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Plugin implementation description goes here.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.api import *
from pyClanSphere.utils import forms
from pyClanSphere.utils.validators import ValidationError, is_not_whitespace_only

from pyClanSphere.plugins.shoutbox.models import ShoutboxEntry

class ShoutboxEntryForm(forms.Form):
    """Post a new entry to the shoutbox."""

    author = forms.TextField(lazy_gettext(u'Author'), max_length=50,
                           validators=[is_not_whitespace_only()])
    text = forms.TextField(lazy_gettext(u'Text'), max_length=255,
                           validators=[is_not_whitespace_only()],
                           widget=forms.Textarea,required=True)

    def __init__(self, entry=None, initial=None):
        if entry is not None:
            initial = forms.fill_dict(initial,
                text=text,
                author=author
            )
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.entry = entry

    @property
    def captcha_protected(self):
        """We're protected if no user is logged in and config says so."""
        return not self.request.user.is_somebody and self.app.cfg['recaptcha_enable']

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.entry = self.entry
        widget.new = self.entry is None
        return widget

    def _set_common_attributes(self, entry):
        forms.set_fields(entry, self.data, 'text')

    def make_entry(self, user=None):
        """A helper function that creates a new game object."""
        entry = ShoutboxEntry(text=self.data['text'])
        self._set_common_attributes(entry)
        if user is None:
            user = get_request().user
        if user.is_somebody:
            entry.set_user(user)
        else:
            entry.set_author(self.data['author'])
        self.entry = entry
        return entry

    def save_changes(self, user):
        """Apply the changes."""
        self._set_common_attributes(self.entry)
