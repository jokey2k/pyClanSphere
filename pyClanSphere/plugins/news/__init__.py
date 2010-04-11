# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.news
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    A news section with good privilege support for editing, creating and publishing

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from os.path import join, dirname

from pyClanSphere.api import _, url_for

from pyClanSphere.plugins.news.database import init_database
from pyClanSphere.plugins.news.models import News
from pyClanSphere.plugins.news.privileges import PLUGIN_PRIVILEGES, NEWS_CREATE, NEWS_EDIT, NEWS_DELETE
from pyClanSphere.plugins.news import views

TEMPLATE_FILES = join(dirname(__file__), 'templates')

def add_admin_links(request, navigation_bar):
    """Add our views to the admin interface"""

    priv_check = request.user.has_privilege

    entries = [('list', url_for('admin/news_list'), _(u'Overview'))]

    if priv_check(NEWS_CREATE) or priv_check(NEWS_EDIT):
        entries.append(('edit', url_for('admin/news_create'), _(u'Write')))

    navigation_bar.insert(1,(('news', url_for('admin/news_list'), _(u'News'), entries)))


def setup(app, plugin):
    """Init our needed stuff"""

    # Setup tables
    init_database()

    # Add our privileges
    for priv in PLUGIN_PRIVILEGES.values():
        app.add_privilege(priv)

    # Add our template path
    app.add_template_searchpath(TEMPLATE_FILES)

    # Register news main page
    app.add_url_rule('/news/', endpoint='news/index', view=views.index)
    app.add_url_rule('/news/page/<int:page>', endpoint='news/index')

    # Register news detail page
    app.add_url_rule('/news/<int:news_id>', endpoint='news/detail',
                     view=views.detail)

    # Register news archive along with archive
    # sub-urls to filter by year, month and day
    app.add_url_rule('/news/archive', endpoint='news/archive',
                     view=views.archive)
    tmp = '/news/archive/'
    for digits, part in zip((0, 0, 0), ('year', 'month', 'day')):
        tmp += '<int(fixed_digits=%d):%s>/' % (digits, part)
        app.add_url_rule(tmp, defaults={'page': 1}, endpoint='news/archive')
        app.add_url_rule(tmp + 'page/<int:page>', endpoint='news/archive')

    # Register our admin views
    app.add_url_rule('/news', prefix='admin', defaults={'page': 1}, endpoint='admin/news_list',
                     view=views.news_list)
    app.add_url_rule('/news/page/<int:page>', prefix='admin', endpoint='admin/news_list',
                     view=views.news_list)
    app.add_url_rule('/news/<int:news_id>', prefix='admin', endpoint='admin/news_edit',
                     view=views.edit_news)
    app.add_url_rule('/news/<int:news_id>/delete', prefix='admin', endpoint='admin/news_delete',
                     view=views.delete_news)
    app.add_url_rule('/news/new', prefix='admin', endpoint='admin/news_create',
                     view=views.edit_news)

    # Add admin views to navigation bar
    app.connect_event('modify-admin-navigation-bar', add_admin_links)

