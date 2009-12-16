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


def add_admin_urls(app, path, idname, listview, editview=None, deleteview=None):
    """Generic admin backend routing function

    As it has become pretty common to use
    /admin/foo/         and
    /admin/foo/page/2   for listings
    /admin/foo/1        for editing
    /admin/foo/new      for creating with None to edit function and
    /admin/foo/1/delete for removals

    just generate the matching urls and endpoints

    editview and/or deleteview may be omitted if they're not needed
    """

    app.add_url_rule('/%s/' % path, prefix='admin', defaults={'page': 1}, endpoint='admin/%s' % path,
                     view=listview)
    app.add_url_rule('/%s/page/<int:page>' % path, prefix='admin', endpoint='admin/%s' % path)
    if editview:
        app.add_url_rule('/%s/new' % path, prefix='admin', endpoint='admin/%s/new' % path,
                         view=editview)
        app.add_url_rule('/%s/<int:%s>' % (path, idname), prefix='admin', endpoint='admin/%s/edit' % path,
                         view=editview)
    if deleteview:
        app.add_url_rule('/%s/<int:%s>/delete' % (path, idname), prefix='admin', endpoint='admin/%s/delete' % path,
                         view=deleteview)
