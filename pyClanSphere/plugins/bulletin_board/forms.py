# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Models for the board.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.api import *
from pyClanSphere.utils import forms

from pyClanSphere.plugins.bulletin_board.models import *

class CategoryForm(forms.Form):
    """Used to edit or create a category"""

    name = forms.TextField(lazy_gettext(u'Name'), required=True, max_length=50)
    order = forms.IntegerField(lazy_gettext(u'Order'), required=True,
                help_text=_('Sorting order, ascending'))
    
    def __init__(self, category, initial=None):
        if category is not None:
            initial = forms.fill_dict(initial,
                name=category.name,
                order=category.order
            )
        elif initial is None:
            initial = forms.fill_dict(initial,
                order=0
            )
        self.category = category
        forms.Form.__init__(self, initial)
    
    def create_category(self):
        """Creates a new category"""
        
        category = Category(self['name'], self['order'])
        db.commit()
        return category
    
    def save_changes(self, category):
        forms.set_fields(category, self.data, 'name', 'order')
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
    order = forms.IntegerField(lazy_gettext(u'Order'),
                help_text=_('Sorting order, ascending'))
    allow_anonymous = forms.BooleanField(lazy_gettext(u'Allow anonymous posting'))
    is_public = forms.BooleanField(lazy_gettext(u'Public'))

    def __init__(self, forum, initial=None):
        if forum is not None:
            initial = forms.fill_dict(initial,
                category=forum.category,
                name=forum.name,
                order=forum.order,
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
                         'allow_anonymous', 'is_public')
        if self.data['order'] is None:
            forum.order = len(self['category'].forums)-1
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