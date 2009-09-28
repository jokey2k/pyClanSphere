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
from pyClanSphere.application import url_for, render_response, emit_event, \
     Response, get_application
from pyClanSphere.i18n import _
from pyClanSphere.utils.pagination import AdminPagination
from pyClanSphere.privileges import assert_privilege
from pyClanSphere.utils import dump_json, ClosingIterator, log
from pyClanSphere.utils.account import flash
from pyClanSphere.utils.text import build_tag_uri
from pyClanSphere.utils.http import redirect_to, redirect
from pyClanSphere.utils.redirects import lookup_redirect
from pyClanSphere.views.admin import render_admin_response, PER_PAGE

from pyClanSphere.plugins.news.forms import NewsForm
from pyClanSphere.plugins.news.models import News
from pyClanSphere.plugins.news.privileges import NEWS_CREATE

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
    
    data = News.query.published().published() \
               .get_list(endpoint='news/index', page=page)

    return render_response('news_index.html', **data)

def archive(req, year=None, month=None, day=None, page=1):
    """Render the monthly archives.

    Available template variables:

        `posts`:
            a list of post objects we want to display

        `pagination`:
            a pagination object to render a pagination

        `year` / `month` / `day`:
            integers or None, useful to entitle the page.

    :Template name: ``archive.html``
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

    newsitems = News.query.limit(PER_PAGE).offset(PER_PAGE * (page - 1)).all()
    pagination = AdminPagination('admin/news_list', page, PER_PAGE,
                                 News.query.count())
    if not newsitems and page != 1:
        raise NotFound()

    can_create = request.user.has_privilege(NEWS_CREATE)
    
    return render_admin_response('admin/news_list.html', 'news.list',
                                 newsitems=newsitems, pagination=pagination,
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
        assert_privilege(NEWS_CREATE)
    else:
        if not newsitem.can_edit(request.user):
            raise Forbidden()

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/news_list')
        elif form.validate(request.form):
            if newsitem is None:
                newsitem = form.make_news(request.user)
                msg = _('The entry %s was created successfully.')
            else:
                form.save_changes()
                msg = _('The entry %s was updated successfully.')

            flash(msg % (escape(newsitem.title)))

            db.commit()
            if 'save_and_continue' in request.form:
                return redirect_to('admin/news_edit', news_id=newsitem.id)
            return form.redirect('admin/news_list')
    return render_admin_response('admin/news_edit.html', 'news.edit',
                                 form=form.as_widget())
