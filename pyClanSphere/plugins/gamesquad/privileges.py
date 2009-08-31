# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.news.privileges
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains a list of available privileges for the gamesquad control.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.api import lazy_gettext
from pyClanSphere.privileges import Privilege, ENTER_ADMIN_PANEL

__all__ = ['PLUGIN_PRIVILEGES']

PLUGIN_PRIVILEGES = {}

def _register(name, description, privilege_dependencies=None):
    """Register a new module privilege."""

    priv = Privilege(name, description, privilege_dependencies)
    PLUGIN_PRIVILEGES[name] = priv
    globals()[name] = priv
    __all__.append(name)

_register('GAME_MANAGE', lazy_gettext(u'can manage games'), ENTER_ADMIN_PANEL)
_register('SQUAD_MANAGE_MEMBERS', lazy_gettext(u'can manage squad memberships'), ENTER_ADMIN_PANEL)
_register('SQUAD_MANAGE', lazy_gettext(u'can manage squads'), SQUAD_MANAGE_MEMBERS)
