# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.war_module
    ~~~~~~~~~~~~~~~~~~~~~~~

    Plugin implementation description goes here.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from os.path import join, dirname, exists
from os import makedirs

from pyClanSphere.api import url_for, _

from pyClanSphere.plugins.war import views
from pyClanSphere.plugins.war.database import init_database
from pyClanSphere.plugins.war.privileges import PLUGIN_PRIVILEGES, WAR_MANAGE

TEMPLATE_FILES = join(dirname(__file__), 'templates')

def add_admin_links(request, navigation_bar):
    """Add our views to the admin interface"""

    priv_check = request.user.has_privilege

    if not priv_check(WAR_MANAGE):
        return

    entries = [('wars', url_for('admin/war_list'), _(u'Wars')),
               ('maps', url_for('admin/warmap_list'), _(u'Maps')),
               ('modes', url_for('admin/warmode_list'), _(u'Modes'))]

    navigation_bar.insert(1, ('war', url_for('admin/war_list'), _(u'War Management'), entries))

def setup(app, plugin):

    # Setup tables
    init_database()

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
    app.add_url_rule('/wars/', prefix='admin', defaults={'page': 1}, endpoint='admin/war_list',
                     view=views.war_list)
    app.add_url_rule('/wars/page/<int:page>', prefix='admin', endpoint='admin/war_list')
    app.add_url_rule('/wars/new', prefix='admin', endpoint='admin/war_create',
                     view=views.war_edit)
    app.add_url_rule('/wars/<int:war_id>', prefix='admin', endpoint='admin/war_edit',
                     view=views.war_edit)
    app.add_url_rule('/wars/<int:war_id>/delete', prefix='admin', endpoint='admin/war_delete',
                     view=views.war_delete)
    app.add_url_rule('/wars/<int:war_id>/result', prefix='admin', endpoint='admin/warresult_edit',
                     view=views.warresult_edit)

    app.add_url_rule('/warmaps/', prefix='admin', defaults={'page': 1}, endpoint='admin/warmap_list',
                     view=views.warmap_list)
    app.add_url_rule('/warmaps/page/<int:page>', prefix='admin', endpoint='admin/warmap_list')
    app.add_url_rule('/warmaps/new', prefix='admin', endpoint='admin/warmap_create',
                     view=views.warmap_edit)
    app.add_url_rule('/warmaps/<int:warmap_id>', prefix='admin', endpoint='admin/warmap_edit',
                     view=views.warmap_edit)
    app.add_url_rule('/warmaps/<int:warmap_id>/delete', prefix='admin', endpoint='admin/warmap_delete',
                     view=views.warmap_delete)

    app.add_url_rule('/warmodes/', prefix='admin', defaults={'page': 1}, endpoint='admin/warmode_list',
                     view=views.warmode_list)
    app.add_url_rule('/warmodes/page/<int:page>', prefix='admin', endpoint='admin/warmode_list')
    app.add_url_rule('/warmodes/new', prefix='admin', endpoint='admin/warmode_create',
                     view=views.warmode_edit)
    app.add_url_rule('/warmodes/<int:warmode_id>', prefix='admin', endpoint='admin/warmode_edit',
                     view=views.warmode_edit)
    app.add_url_rule('/warmodes/<int:warmode_id>/delete', prefix='admin', endpoint='admin/warmode_delete',
                     view=views.warmode_delete)

    # Add admin views to navigation bar
    app.connect_event('modify-admin-navigation-bar', add_admin_links)

    # create warmaps folder if not already there
    map_path = join(app.instance_folder, 'warmaps')
    if not exists(map_path):
        makedirs(map_path)
