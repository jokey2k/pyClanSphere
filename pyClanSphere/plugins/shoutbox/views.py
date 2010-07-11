# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.shoutbox.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements all the views and Widgets for the shoutbox module.

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug import escape
from werkzeug.exceptions import NotFound

from pyClanSphere.api import db, url_for, get_request
from pyClanSphere.application import render_response
from pyClanSphere.privileges import assert_privilege
from pyClanSphere.utils.http import get_redirect_target
from pyClanSphere.widgets import Widget

from pyClanSphere.plugins.shoutbox.forms import ShoutboxEntryForm, DeleteShoutboxEntryForm
from pyClanSphere.plugins.shoutbox.models import ShoutboxEntry
from pyClanSphere.plugins.shoutbox.privileges import SHOUTBOX_MANAGE

class ShoutboxWidget(Widget):
    """Show Entries in Widget format"""

    name = 'Shoutbox'
    template = 'widgets/shoutbox.html'

    def __init__(self, show_title=True, title=u'Shoutbox', entrycount=10, hide_form=False):
        super(ShoutboxWidget, self).__init__()
        self.title = title
        self.show_title = show_title
        self.hide_form = hide_form
        self.entries = ShoutboxEntry.query.order_by(ShoutboxEntry.postdate.desc()) \
                                    .limit(entrycount).all()
        self.newposturl = escape(url_for('shoutbox/post', next=get_request().path))

def make_shoutbox_entry(request):
    """Render form to make a shoutbox entry.

    Available template variables:

        `form`:
            form object with all required fields

        `widgetoptions`:
            redirected widgetoptions to hide post button below entries

    :Template name: ``shoutbox_post.html``
    :URL endpoint: ``shoutbox/post``
    """

    form = ShoutboxEntryForm()

    if request.method == 'POST':
        if request.user.is_somebody:
            form.disable_author()
        if form.validate(request.form):
            entry = form.make_entry()
            db.commit()
            # as this affects pretty much all visible pages, we flush cache here
            request.app.cache.clear()
            target = get_redirect_target()
            return form.redirect(target if target is not None else 'core/index')

    return render_response('shoutbox_post.html', form=form.as_widget(),
                           widgetoptions=['hide_shoutbox_note'])

def delete_shoutbox_entry(request, entry_id):
    """Render form to delete a shoutbox entry.

    Available template variables:

        `form`:
            form object with all required fields

    :Template name: ``shoutbox_post.html``
    :URL endpoint: ``shoutbox/post``
    """

    entry = ShoutboxEntry.query.get(entry_id)
    if entry is None:
        raise NotFound()

    form = DeleteShoutboxEntryForm(entry)
    assert_privilege(SHOUTBOX_MANAGE)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('core/index')
        if form.validate(request.form):
            form.add_invalid_redirect_target('shoutbox/delete', entry_id=entry.id)
            form.delete_entry()
            db.commit()
            # as this affects pretty much all visible pages, we flush cache here
            request.app.cache.clear()
            return form.redirect('core/index')

    return render_response('shoutbox_delete.html', form=form.as_widget())
