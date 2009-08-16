# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.news.privileges
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains a list of used privileges for the news plugin.

    :copyright: (c) 2009 by the Zine Team, see AUTHORS for more details.
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

_register('NEWS_CREATE', lazy_gettext(u'can create news'), ENTER_ADMIN_PANEL)
_register('NEWS_EDIT', lazy_gettext(u'can edit non-selfwritten news'), ENTER_ADMIN_PANEL)
_register('NEWS_PUBLIC', lazy_gettext(u'can work on published items or publish new ones'), NEWS_EDIT)
_register('NEWS_DELETE', lazy_gettext(u'can delete news'), ENTER_ADMIN_PANEL)
