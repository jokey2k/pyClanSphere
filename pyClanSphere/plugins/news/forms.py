# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.news.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Forms we gonna need to handle creation and editing of entries

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.api import *
from pyClanSphere.utils import forms
from pyClanSphere.utils.validators import ValidationError

from pyClanSphere.plugins.news.models import News, \
     STATUS_DRAFT, STATUS_PUBLISHED
from pyClanSphere.plugins.news.privileges import NEWS_DELETE

class NewsForm(forms.Form):
    """The form for news writing."""

    title = forms.TextField(lazy_gettext(u'Title'), required=True)
    text = forms.TextField(lazy_gettext(u'News'), required=True, max_length=65000,
                           widget=forms.Textarea)
    pub_date = forms.DateTimeField(lazy_gettext(u'Date of Publication'))
    status = forms.ChoiceField(lazy_gettext(u'Status'))

    def __init__(self, news=None, initial=None):
        if news is not None:
            initial = forms.fill_dict(initial,
                title=news.title,
                text=news.text,
                status=news.status,
                pub_date=news.pub_date,
                author=news.author
            )
        else:
            initial = forms.fill_dict(initial, status=STATUS_DRAFT)

            # if we have a request, we can use the current user as a default
            req = get_request()
            if req and req.user:
                initial['author'] = req.user

        forms.Form.__init__(self, initial)
        self.news = news
        self.status.choices = [
            (STATUS_DRAFT, _('Draft')),
            (STATUS_PUBLISHED, _('Published'))
        ]

    def validate_status(self, status):
        """Users without NEWS_PUBLIC are not allowed to switch status flag"""

        if not self.news and status == STATUS_PUBLISHED:
            raise ValidationError(_(u'Initially news should always be drafts'))

        if status == STATUS_PUBLISHED and not \
                self.news.can_publish():
            raise ValidationError(_(u'You have no permission to publish posts.'))

    def _set_common_attributes(self, news):
        forms.set_fields(news, self.data, 'title', 'text', 'status', 'pub_date')

    def make_news(self, user):
        """A helper function that creates a new user object."""
        news = News("", user, "")
        self._set_common_attributes(news)
        news.touch_times()
        self.news = news
        return news

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.news = self.news
        widget.new = self.news is None

        req = get_request()
        if req and req.user:
            widget.user_can_delete = req.user.has_privilege(NEWS_DELETE)

        return widget

    def save_changes(self):
        """Apply the changes."""
        self._set_common_attributes(self.news)
        self.news.touch_times(self.data['pub_date'])


class DeleteNewsForm(forms.Form):
    """Used to remove a newsitem."""

    def __init__(self, newsitem, initial=None):
        forms.Form.__init__(self, initial)
        self.newsitem = newsitem

    def delete_news(self):
        """Deletes the user."""
        db.delete(self.newsitem)

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.newsitem = self.newsitem
        return widget
