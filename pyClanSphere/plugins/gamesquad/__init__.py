# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Game / Squad / Member Group Management

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from os.path import join, dirname

from pyClanSphere.api import _, url_for, signals, signal
from pyClanSphere.utils.account import add_account_urls
from pyClanSphere.utils.admin import add_admin_urls

from pyClanSphere.plugins.gamesquad.database import init_database
from pyClanSphere.plugins.gamesquad.models import SquadMember
from pyClanSphere.plugins.gamesquad.privileges import PLUGIN_PRIVILEGES, GAME_MANAGE, LEVEL_MANAGE
from pyClanSphere.plugins.gamesquad import views


TEMPLATE_FILES = join(dirname(__file__), 'templates')

# Register our used signals
signal('before_game_deleted', """\
Plugins can use this to react to game deletes.  They can't stop
the deleting of the game but they can delete information in
their own tables so that the database is consistent afterwards.

:keyword game: the game to be deleted
:keyword formdata: data of the submitted form
""")
signal('before_squad_deleted', """\
Plugins can use this to react to squad deletes.  They can't stop
the deleting of the squad but they can delete information in
their own tables so that the database is consistent afterwards.

:keyword squad: the squad to be deleted
:keyword formdata: data of the submitted form
""")
signal('before_level_deleted', """\
Plugins can use this to react to level deletes.  They can't stop
the deleting of the level but they can delete information in
their own tables so that the database is consistent afterwards.

:keyword level: the level to be deleted
:keyword formdata: data of the submitted form
""")
signal('before_gameaccount_deleted', """\
Plugins can use this to react to gameaccount deletes.  They can't stop
the deleting of the level but they can delete information in
their own tables or push out new server configurations.

:keyword gameaccount: the gameaccount to be deleted
""")

def add_admin_links(sender, **kwds):
    """Add our views to the admin interface"""

    priv_check = kwds['request'].user.has_privilege

    entries = [('squads', url_for('admin/squads'), _(u'Squads'))]

    if priv_check(GAME_MANAGE):
        entries.insert(0,('games', url_for('admin/games'), _(u'Games')))

    if priv_check(LEVEL_MANAGE):
        entries.append(('levels', url_for('admin/levels'), _(u'Levels')))

    kwds['navbar'].insert(1, ('gamesquad', url_for('admin/squads'), _(u'Games and Squads'), entries))

def user_deleted_memberships(sender, **kwds):
    """Delete memberships of a user that will be deleted"""

    user = kwds['user']
    
    memberships = SquadMember.query.filter_by(user=me).all()

    for membership in memberships:
      db.delete(membership)

    db.commit()

def add_account_links(sender, **kwds):
    """Add our views to the account interface"""

    kwds['navbar'].insert(2, ('gameaccounts', url_for('account/gameaccounts'), _(u'Gameaccounts'),[]))

def setup(app, plugin):
    """Init our needed stuff"""

    # Setup tables
    init_database(app)

    # Add our privileges
    for priv in PLUGIN_PRIVILEGES.values():
        app.add_privilege(priv)

    # Add our template path
    app.add_template_searchpath(TEMPLATE_FILES)

    # Register pages page
    app.add_url_rule('/games/', endpoint='game/index', defaults={'page': 1},
                     view=views.game_index)
    app.add_url_rule('/games/page/<int:page>', endpoint='game/index',
                     view=views.game_index)
    app.add_url_rule('/games/<int:game_id>', endpoint='game/detail',
                     view=views.game_detail)
    app.add_url_rule('/squads/<int:squad_id>', endpoint='squad/detail',
                     view=views.squad_detail)

    # Register our admin views
    # Games
    add_admin_urls(app, 'games', 'game_id', views.game_list,
                   views.edit_game, views.delete_game)

    # Squads
    add_admin_urls(app, 'squads', 'squad_id', views.squad_list,
                   views.edit_squad, views.delete_squad)

    # Levels
    add_admin_urls(app, 'levels', 'level_id', views.level_list,
                   views.edit_level, views.delete_level)

    # Squadmembers
    app.add_url_rule('/squads/<int:squad_id>/members', prefix='admin', defaults={'page': 1}, endpoint='admin/squadmembers',
                     view=views.list_squadmembers)
    app.add_url_rule('/squads/<int:squad_id>/members/page/<int:page>', prefix='admin', endpoint='admin/squadembers')
    app.add_url_rule('/squads/<int:squad_id>/members/<int:user_id>/edit', prefix='admin', endpoint='admin/squadmembers/edit',
                     view=views.edit_squadmember)
    app.add_url_rule('/squads/<int:squad_id>/members/new', prefix='admin', endpoint='admin/squadmembers/new',
                     view=views.edit_squadmember)
    app.add_url_rule('/squads/<int:squad_id>/members/<int:user_id>/delete', prefix='admin', endpoint='admin/squadmembers/delete',
                     view=views.delete_squadmember)

    # Admin views: Gameaccounts
    app.add_url_rule('/gameaccounts/<int:account_id>/delete', prefix='admin', endpoint='admin/gameaccounts/delete',
                      view=views.adm_delete_gameaccount)

    # Account views: Gameaccounts
    add_account_urls(app, 'gameaccounts', 'account_id', views.gameaccount_list,
                     views.gameaccount_edit, views.acc_delete_gameaccount)

    # Delete squadmember entries while a user is being deleted
    signals.before_user_deleted.connect(user_deleted_memberships)

    # Add admin views to navigation bar
    signals.modify_admin_navigation_bar.connect(add_admin_links)

    # Add account views to navigation bar
    signals.modify_account_navigation_bar.connect(add_account_links)
