# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.war
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This plugin allows tracking of clanwars

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from os.path import join, dirname, exists
from os import makedirs

from pyClanSphere.api import url_for, _, signals
from pyClanSphere.utils.admin import add_admin_urls

from pyClanSphere.plugins.war import views
from pyClanSphere.plugins.war.database import init_database
from pyClanSphere.plugins.war.privileges import PLUGIN_PRIVILEGES, WAR_MANAGE

TEMPLATE_FILES = join(dirname(__file__), 'templates')

def add_admin_links(sender, **kwds):
    """Add our views to the admin interface"""

    priv_check = kwds['request'].user.has_privilege

    if not priv_check(WAR_MANAGE):
        return

    entries = [('wars', url_for('admin/wars'), _(u'Wars')),
               ('maps', url_for('admin/warmaps'), _(u'Maps')),
               ('modes', url_for('admin/warmodes'), _(u'Modes'))]

    kwds['navbar'].insert(1, ('war', url_for('admin/wars'), _(u'War Management'), entries))

def setup(app, plugin):
    # Setup tables
    init_database(app)

    # Register repository for schema updates
    app.register_upgrade_repository(plugin, dirname(__file__))

    # Add our privileges
    for priv in PLUGIN_PRIVILEGES.values():
        app.add_privilege(priv)

    # Add our template path
    app.add_template_searchpath(TEMPLATE_FILES)

    # war related pages
    app.add_url_rule('/wars/', endpoint='wars/index', defaults={'page': 1},
                     view=views.war_index)
    app.add_url_rule('/wars/page/<int:page>', endpoint='wars/index')
    app.add_url_rule('/wars/<int:war_id>', endpoint='wars/detail',
                     view=views.war_detail)
    app.add_url_rule('/wars/fightus', endpoint='wars/fightus',
                     view=views.war_fightus)

    # Admin views
    add_admin_urls(app, 'wars', 'war_id', views.war_list,
                   views.war_edit, views.war_delete)
    app.add_url_rule('/wars/<int:war_id>/result', prefix='admin', endpoint='admin/warresult_edit',
                     view=views.warresult_edit)

    add_admin_urls(app, 'warmaps', 'warmap_id', views.warmap_list,
                   views.warmap_edit, views.warmap_delete)
    add_admin_urls(app, 'warmodes', 'warmode_id', views.warmode_list,
                   views.warmode_edit, views.warmode_delete)

    # Add admin views to navigation bar
    signals.modify_admin_navigation_bar.connect(add_admin_links)

    # create warmaps folder if not already there
    map_path = join(app.instance_folder, 'warmaps')
    if not exists(map_path):
        makedirs(map_path)
