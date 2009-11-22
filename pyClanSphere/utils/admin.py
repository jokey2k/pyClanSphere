# -*- coding: utf-8 -*-
"""
    pyClanSphere.utils.admin
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements various functions used by the admin interface.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
from time import time
from itertools import islice
from datetime import datetime

from jinja2 import Markup
from werkzeug import url_quote

from pyClanSphere.privileges import ENTER_ADMIN_PANEL, require_privilege
from pyClanSphere.utils import local, load_json
from pyClanSphere.utils.net import open_url
from pyClanSphere.i18n import _


def flash(msg, type='info'):
    """Add a message to the message flash buffer.

    The default message type is "info", other possible values are
    "add", "remove", "error", "ok" and "configure". The message type affects
    the icon and visual appearance.

    The flashes messages appear only in the admin interface!
    """
    assert type in \
        ('info', 'add', 'remove', 'error', 'ok', 'configure', 'warning')
    if type == 'error':
        msg = (u'<strong>%s:</strong> ' % _('Error')) + msg
    if type == 'warning':
        msg = (u'<strong>%s:</strong> ' % _('Warning')) + msg

    local.request.session.setdefault('admin/flashed_messages', []).\
            append((type, Markup(msg)))


def require_admin_privilege(expr=None):
    """Works like `require_privilege` but checks if the rule for
    `ENTER_ADMIN_PANEL` exists as well.
    """
    if expr:
        expr = ENTER_ADMIN_PANEL & expr
    else:
        expr = ENTER_ADMIN_PANEL
    return require_privilege(expr)
