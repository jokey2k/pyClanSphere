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
from pyClanSphere.utils import htmlhelpers
from pyClanSphere.utils.admin import add_admin_urls

from pyClanSphere.plugins.bulletin_board import views
from pyClanSphere.plugins.bulletin_board.models import *
from pyClanSphere.plugins.bulletin_board.database import init_database
from pyClanSphere.plugins.bulletin_board.privileges import PLUGIN_PRIVILEGES, BOARD_MANAGE
from pyClanSphere.plugins.bulletin_board.services import do_get_post

SHARED_FILES = join(dirname(__file__), 'shared')
TEMPLATE_FILES = join(dirname(__file__), 'templates')

signal('before_board_category_deleted', """\
Plugins can use this to react to board category deletes.  They can't stop
the deleting but they can delete information in their own tables so that
the database is consistent afterwards.

:keyword category: the category to be deleted
:keyword formdata: data of the submitted form
""")
signal('before_board_forum_squad_deleted', """\
Plugins can use this to react to board forum deletes.  They can't stop
the deleting but they can delete information in their own tables so that
the database is consistent afterwards.

:keyword forum: the forum to be deleted
:keyword formdata: data of the submitted form
""")

def inject_js(sender, **kwds):
    """We add some jquery routines, so load them in the header"""

    kwds['result'].append(
        htmlhelpers.script(shared_url('bulletin_board::js/bulletin_board.js'))
    )

def add_admin_links(sender, **kwds):
    """Add our views to the admin interface"""

    priv_check = kwds['request'].user.has_privilege

    if not priv_check(BOARD_MANAGE):
        return

    entries = [('categories', url_for('admin/board/categories'), _(u'Categories')),
               ('forums', url_for('admin/board/forums'), _(u'Forums'))
    ]

    kwds['navbar'].insert(1, ('board', url_for('admin/board/categories'), _(u'Board'), entries))

def setup(app, plugin):
    # Add our privileges
    for priv in PLUGIN_PRIVILEGES.values():
        app.add_privilege(priv)

    # init new tables
    init_database(app)

    # Add our template path
    app.add_template_searchpath(TEMPLATE_FILES)

    # Add shared data path
    app.add_shared_exports('bulletin_board', SHARED_FILES)

    # Register frontend views
    app.add_url_rule('/board/', endpoint='board/index', view=views.board_index)
    app.add_url_rule('/board/forum/<int:forum_id>', endpoint='board/topics', defaults={'page': 1}, view=views.topic_list)
    app.add_url_rule('/board/forum/<int:forum_id>/page/<int:page>', endpoint='board/topics')
    app.add_url_rule('/board/topic/<int:topic_id>', endpoint='board/topic_detail', defaults={'page': 1}, view=views.topic_detail)
    app.add_url_rule('/board/topic/<int:topic_id>/page/<int:page>', endpoint='board/topic_detail')
    app.add_url_rule('/board/post/<int:post_id>', endpoint='board/post_find', view=views.topic_by_post)
    app.add_url_rule('/board/post/<int:post_id>/edit', endpoint='board/post_edit', view=views.post_edit)
    app.add_url_rule('/board/post/<int:post_id>/delete', endpoint='board/post_delete', view=views.post_delete)

    # Register our admin views
    add_admin_urls(app, 'board/categories', 'category_id',
                   views.categories_list, views.category_edit,
                   views.category_delete)
    add_admin_urls(app, 'board/forums', 'forum_id',
                   views.forum_list, views.forum_edit, views.forum_delete)

    # Add admin views to navigation bar
    signals.modify_admin_navigation_bar.connect(add_admin_links)

    # Inject our js for post quoting
    signals.before_metadata_assembled.connect(inject_js)

    # Add JSON services
    app.add_servicepoint('bulletin_board/get_post', do_get_post)
