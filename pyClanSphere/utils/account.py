# -*- coding: utf-8 -*-
"""
    pyClanSphere.utils.account
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements various functions used by the account interface.

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.privileges import ENTER_ACCOUNT_PANEL, require_privilege
from pyClanSphere.utils import local
from pyClanSphere.i18n import _


def flash(msg, type='info'):
    """Add a message to the message flash buffer.

    The default message type is "info", other possible values are
    "add", "remove", "error", "ok" and "configure". The message type affects
    the icon and visual appearance.

    The flashes messages appear only in the account interface!
    """
    assert type in \
        ('info', 'add', 'remove', 'error', 'ok', 'configure', 'warning')
    if type == 'error':
        msg = (u'<strong>%s:</strong> ' % _('Error')) + msg
    if type == 'warning':
        msg = (u'<strong>%s:</strong> ' % _('Warning')) + msg

    local.request.session.setdefault('account/flashed_messages', []).\
            append((type, msg))


def require_account_privilege(expr=None):
    """Works like `require_privilege` but checks if the rule for
    `ENTER_ADMIN_PANEL` exists as well.
    """
    if expr:
        expr = ENTER_ACCOUNT_PANEL & expr
    else:
        expr = ENTER_ACCOUNT_PANEL
    return require_privilege(expr)


def add_account_urls(app, path, idname, listview, editview=None, deleteview=None):
    """Generic admin backend routing function

    As it has become pretty common to use
    /account/foo/         and
    /account/foo/page/2   for listings
    /account/foo/1        for editing
    /account/foo/new      for creating with None to edit function and
    /account/foo/1/delete for removals

    just generate the matching urls and endpoints

    editview and/or deleteview may be omitted if they're not needed
    """

    app.add_url_rule('/%s/' % path, prefix='account', defaults={'page': 1}, endpoint='account/%s' % path,
                     view=listview)
    app.add_url_rule('/%s/page/<int:page>' % path, prefix='account', endpoint='account/%s' % path)
    if editview:
        app.add_url_rule('/%s/new' % path, prefix='account', endpoint='account/%s/new' % path,
                         view=editview)
        app.add_url_rule('/%s/<int:%s>' % (path, idname), prefix='account', endpoint='account/%s/edit' % path,
                         view=editview)
    if deleteview:
        app.add_url_rule('/%s/<int:%s>/delete' % (path, idname), prefix='account', endpoint='account/%s/delete' % path,
                         view=deleteview)
