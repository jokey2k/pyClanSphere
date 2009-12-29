# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Forms we use for the board.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime

from pyClanSphere.api import *
from pyClanSphere.utils import forms
from pyClanSphere.utils.validators import is_not_whitespace_only

from pyClanSphere.plugins.bulletin_board.models import *

class CategoryForm(forms.Form):
    """Used to edit or create a category"""

    name = forms.TextField(lazy_gettext(u'Name'), required=True, max_length=50)
    ordering = forms.IntegerField(lazy_gettext(u'Order'),
                help_text=_('Sorting order, ascending'))
    
    def __init__(self, category, initial=None):
        if category is not None:
            initial = forms.fill_dict(initial,
                name=category.name,
                ordering=category.ordering
            )
        self.category = category
        forms.Form.__init__(self, initial)
    
    def create_category(self):
        """Creates a new category"""
        
        category = Category(self['name'])
        self.save_changes(category)
        return category
    
    def save_changes(self, category):
        forms.set_fields(category, self.data, 'name', 'ordering')
        if self.data['ordering'] is None:
            category.ordering = category.forums.count()-1
        else:
            category.ordering = self.data['ordering']
        if category.ordering < 0:
            category.ordering = 0
        db.commit()

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.new = self.category is None
        return widget


class DeleteCategoryForm(forms.Form):
    """Used to delete a category"""
    
    action = forms.ChoiceField(lazy_gettext(u'What should pyClanSphere do with forums '
                                            u'assigned to this category?'),
                              choices=[
        ('delete', lazy_gettext(u'Delete category, delete forums and posts')),
        ('relocate', lazy_gettext(u'Move the forums to another category'))
    ], widget=forms.RadioButtonGroup)
    relocate_to = forms.ModelField(Category, 'id', lazy_gettext(u'Relocate forums to'),
                                   widget=forms.SelectBox)

    def __init__(self, category, initial=None):
        self.category = category
        self.relocate_to.choices = [('', u'')] + [
            (c.id, c.name) for c in Category.query.filter(Category.id != category.id)
        ]

        forms.Form.__init__(self, forms.fill_dict(initial,
            action='delete'))

    def context_validate(self, data):
        if data['action'] == 'relocate' and not data['relocate_to']:
            raise ValidationError(_('You have to select a category which '
                                    'the forums get assigned to.'))

    def delete_category(self):
        """Deletes a category."""

        if self.data['action'] == 'relocate':
            for forum in self.category.forums:
                forum.category = self['relocate_to']

        emit_event('before-board-category-deleted', self.category, self.data)

        db.delete(self.category)
        db.commit()


class ForumForm(forms.Form):
    """Used to edit or create a forum"""

    category = forms.ModelField(Category, 'id', lazy_gettext(u'Category'),
                                required=True, widget=forms.SelectBox)
    name = forms.TextField(lazy_gettext(u'Name'), required=True,
                           max_length=50)
    description = forms.TextField(lazy_gettext(u'Description'), max_length=255)
    ordering = forms.IntegerField(lazy_gettext(u'Order'),
                help_text=_('Sorting order, ascending'))
    allow_anonymous = forms.BooleanField(lazy_gettext(u'Allow anonymous posting'))
    is_public = forms.BooleanField(lazy_gettext(u'Public'))

    def __init__(self, forum, initial=None):
        if forum is not None:
            initial = forms.fill_dict(initial,
                category=forum.category,
                name=forum.name,
                ordering=forum.ordering,
                allow_anonymous=forum.allow_anonymous,
                is_public=forum.is_public
            )
        elif initial is None:
            initial = forms.fill_dict(initial,
                allow_anonymous=False,
                is_public=True
            )
        self.forum = forum
        self.category.choices = [(c.id, c.name) for c in Category.query.all()]
        forms.Form.__init__(self, initial)

    def create_forum(self):
        """Creates a new forum"""

        forum = Forum(self['category'])
        self.save_changes(forum)
        return forum

    def save_changes(self, forum):
        forms.set_fields(forum, self.data, 'category', 'name',
                         'allow_anonymous', 'description', 'is_public')
        if self.data['ordering'] is None:
            forum.ordering = self['category'].forums.count()-1
        else:
            forum.ordering = self.data['ordering']
        if forum.ordering < 0:
            forum.ordering = 0
        db.commit()

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.new = self.forum is None
        return widget


class DeleteForumForm(forms.Form):
    """Used to delete a forum"""

    action = forms.ChoiceField(lazy_gettext(u'What should pyClanSphere do with topics '
                                            u'assigned to this forum?'),
                              choices=[
        ('delete', lazy_gettext(u'Delete forum, delete topics and posts')),
        ('relocate', lazy_gettext(u'Move the topics to another forum'))
    ], widget=forms.RadioButtonGroup)
    relocate_to = forms.ModelField(Forum, 'id', lazy_gettext(u'Relocate topics to'),
                                   widget=forms.SelectBox)

    def __init__(self, forum, initial=None):
        self.forum = forum
        self.relocate_to.choices = [('', u'')] + [
            (c.id, c.name) for c in Forum.query.filter(Forum.id != forum.id)
        ]

        forms.Form.__init__(self, forms.fill_dict(initial,
            action='delete'))

    def context_validate(self, data):
        if data['action'] == 'relocate' and not data['relocate_to']:
            raise ValidationError(_('You have to select a forum which '
                                    'the topics get assigned to.'))

    def delete_forum(self):
        """Deletes a forum."""
        new_forum = self['relocate_to']
        if self.data['action'] == 'relocate':
            for topic in self.forum.topics:
                topic.forum = new_forum

        emit_event('before-board-forum-deleted', self.forum, self.data)

        db.delete(self.forum)
        db.commit()

        if self.data['action'] == 'relocate':
            new_forum.refresh()

class PostForm(forms.Form):
    """Post creation and edit"""

    yourname = forms.TextField(lazy_gettext(u'Your Name'), max_length=40)
    title = forms.TextField(lazy_gettext(u'Title'), max_length=255)
    _maxtext = 5000
    text = forms.TextField(lazy_gettext(u'Text'), max_length=_maxtext,
                           widget=forms.Textarea,
                           validators=[is_not_whitespace_only()])

    def __init__(self, target, post=None, user=None, initial=None):
        assert target is not None
        if post is not None:
            initial = forms.fill_dict(initial,
                text = post.text,
            )
        forms.Form.__init__(self, initial)
        self.user = user or self.request.user
        self.target = target
        self.topic = None
        if isinstance(target, Topic):
            self.topic = target

    @property
    def captcha_protected(self):
        """We're protected if no user is logged in and config says so."""
        return not self.request.user.is_somebody and self.request.app.cfg['recaptcha_enable']

    def context_validate(self, data):
        topic = self.topic
        if topic and topic.lastpost.text == data['text']:
            raise ValidationError(_("No Doublepost"))

    def create_topic(self, forum, user):
        """Create a topic for our new post"""
        
        assert forum is not None
        topic = Topic(forum, self['title'], user)
        db.commit()
        return topic
    
    def create_post(self):
        """Create a new post"""
        
        user = self.user
        if not self.user.is_somebody:
            user = self['yourname']

        topic = self.topic
        if topic is None:
            topic = self.create_topic(self.target, user)
        
        post = Post(topic, self['text'], user, datetime.utcnow(), self.request.remote_addr)
        db.commit()
        
        topic.refresh()
        db.commit()
        
        return post

    def save_changes(self, post):
        forms.set_fields(post, self.data, 'text')
        db.commit()
