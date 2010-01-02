# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of a simple bulletin board.
    People which use complete management sites don't use
    that many advanced features found in popular forums software anyway.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from os.path import join, dirname

from pyClanSphere.api import *
from pyClanSphere.utils.admin import add_admin_urls

from pyClanSphere.plugins.bulletin_board import views
from pyClanSphere.plugins.bulletin_board.models import *
from pyClanSphere.plugins.bulletin_board.models import init_database
from pyClanSphere.plugins.bulletin_board.privileges import PLUGIN_PRIVILEGES, BOARD_MANAGE

TEMPLATE_FILES = join(dirname(__file__), 'templates')

def add_admin_links(request, navigation_bar):
    """Add our views to the admin interface"""

    priv_check = request.user.has_privilege

    entries = [('categories', url_for('admin/board/categories'), _(u'Categories')),
               ('forums', url_for('admin/board/forums'), _(u'Forums'))
    ]

    if priv_check(BOARD_MANAGE):
        navigation_bar.insert(1, ('board', url_for('admin/board/categories'), _(u'Board'), entries))

def setup(app, plugin):
    # Add our privileges
    for priv in PLUGIN_PRIVILEGES.values():
        app.add_privilege(priv)

    # init new tables
    init_database(app)

    # Add our template path
    app.add_template_searchpath(TEMPLATE_FILES)

    # Register frontend views
    app.add_url_rule('/board/', endpoint='board/index', view=views.board_index)
    app.add_url_rule('/board/forum/<int:forum_id>', endpoint='board/topics', defaults={'page': 1}, view=views.topic_list)
    app.add_url_rule('/board/forum/<int:forum_id>/page/<int:page>', endpoint='board/topics')
    app.add_url_rule('/board/topic/<int:topic_id>', endpoint='board/topic_detail', defaults={'page': 1}, view=views.topic_detail)
    app.add_url_rule('/board/topic/<int:topic_id>/page/<int:page>', endpoint='board/topic_detail')
    app.add_url_rule('/board/post/<int:post_id>', endpoint='board/post_find', view=views.topic_by_post)
    app.add_url_rule('/board/post/<int:post_id>/edit', endpoint='board/post_edit', view=views.post_edit)

    # Register our admin views
    add_admin_urls(app, 'board/categories', 'category_id',
                   views.categories_list, views.category_edit,
                   views.category_delete)
    add_admin_urls(app, 'board/forums', 'forum_id',
                   views.forum_list, views.forum_edit, views.forum_delete)

    # Add admin views to navigation bar
    app.connect_event('modify-admin-navigation-bar', add_admin_links)
