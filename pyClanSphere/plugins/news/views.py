# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.news.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements all the views for the news module.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from os.path import exists
from time import asctime, gmtime, time
from datetime import date

from werkzeug import escape
from werkzeug.exceptions import NotFound, Forbidden

from pyClanSphere import cache
from pyClanSphere.database import db
from pyClanSphere.application import url_for, render_response, \
     get_application
from pyClanSphere.i18n import _
from pyClanSphere.utils.pagination import AdminPagination
from pyClanSphere.privileges import assert_privilege
from pyClanSphere.utils import log
from pyClanSphere.utils.admin import require_admin_privilege, flash as admin_flash
from pyClanSphere.utils.text import build_tag_uri
from pyClanSphere.utils.http import redirect_to, redirect
from pyClanSphere.utils.redirects import lookup_redirect
from pyClanSphere.views.admin import render_admin_response, PER_PAGE

from pyClanSphere.plugins.news import privileges
from pyClanSphere.plugins.news.forms import NewsForm, DeleteNewsForm
from pyClanSphere.plugins.news.models import News

# Public views

@cache.response(vary=('user',))
def index(req, page=1):
    """Render the most recent posts.

    Available template variables:

        `newsitems`:
            a list of post objects we want to display

        `pagination`:
            a pagination object to render a pagination

    :Template name: ``index.html``
    :URL endpoint: ``news/index``
    """

    data = News.query.published() \
               .get_list(endpoint='news/index', page=page)

    return render_response('news_index.html', **data)

@cache.response(vary=('user',))
def detail(req, news_id):
    """Render the given post.

    Available template variables:

        `newsitem`:
            the item we want to display

    :Template name: ``news_detail.html``
    :URL endpoint: ``news/detail``
    """

    entry = News.query.get(news_id)
    if not entry or (entry and not entry.is_public and not req.user.is_somebody):
        raise NotFound()

    return render_response('news_detail.html', newsitem=entry)

@cache.response(vary=('user',))
def archive(req, year=None, month=None, day=None, page=1):
    """Render the monthly archives.

    Available template variables:

        `posts`:
            a list of post objects we want to display

        `pagination`:
            a pagination object to render a pagination

        `year` / `month` / `day`:
            integers or None, useful to entitle the page.

    :Template name: ``news_archive.html``
    :URL endpoint: ``news/archive``
    """

    if not year:
        return render_response('news_archive.html', month_list=True,
                               **News.query.published() \
                                     .get_archive_summary())

    url_args = dict(year=year, month=month, day=day)
    per_page = 20
    data = News.query.published().date_filter(year, month, day) \
               .get_list(page=page, endpoint='news/archive',
                         url_args=url_args, per_page=per_page)

    return render_response('news_archive.html', year=year, month=month, day=day,
                           date=date(year, month or 1, day or 1),
                           month_list=False, **data)

# Admin views

def news_list(request, page):
    """Show all news in a list."""

    data = News.query.get_list('admin/news', page, request.per_page)

    can_create = request.user.has_privilege(privileges.NEWS_CREATE)

    return render_admin_response('admin/news_list.html', 'news.list',
                                 newsitems=data['newsitems'], pagination=data['pagination'],
                                 can_create=can_create)


def edit_news(request, news_id=None):
    """Edit an existing entry or create a new one."""

    newsitem = None
    if news_id is not None:
        newsitem = News.query.get(news_id)
        if newsitem is None:
            raise NotFound()
    form = NewsForm(newsitem)

    if newsitem is None:
        assert_privilege(privileges.NEWS_CREATE)
    else:
        if not newsitem.can_edit(request.user):
            raise Forbidden()

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/news')
        elif 'delete' in request.form:
            return redirect_to('admin/news/delete', news_id=news_id)
        elif form.validate(request.form):
            if newsitem is None:
                newsitem = form.make_news(request.user)
                msg = _('The entry %s was created successfully.')
            else:
                form.save_changes()
                msg = _('The entry %s was updated successfully.')

            admin_flash(msg % (escape(newsitem.title)))

            db.commit()
            if 'save_and_continue' in request.form:
                return redirect_to('admin/news_edit', news_id=newsitem.id)
            return redirect_to('admin/news')
    return render_admin_response('admin/news_edit.html', 'news.edit',
                                 form=form.as_widget())

@require_admin_privilege(privileges.NEWS_DELETE)
def delete_news(request, news_id=None):
    """Remove given news entry"""

    newsitem = News.query.get(news_id)
    if newsitem is None:
        raise NotFound()
    form = DeleteNewsForm(newsitem)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/news/edit', news_id=news_id)
        elif 'confirm' in request.form and form.validate(request.form):
            title = str(newsitem.title)
            form.delete_news()
            db.commit()
            admin_flash(_('The entry %s was deleted successfully') % title, 'remove')
            return redirect_to('admin/news')

    return render_admin_response('admin/news_delete.html', 'news.edit',
                                 form=form.as_widget())
