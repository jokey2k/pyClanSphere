# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board.privileges
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains a list of available privileges for the board plugin.

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

_register('BOARD_MODERATE', lazy_gettext(u'can moderate posts'))
_register('BOARD_MANAGE', lazy_gettext(u'can manage forums'), ENTER_ADMIN_PANEL)
