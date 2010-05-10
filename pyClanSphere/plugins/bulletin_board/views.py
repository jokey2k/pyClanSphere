# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements all the views for the board module.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug import escape
from werkzeug.exceptions import NotFound, Forbidden

from pyClanSphere import cache
from pyClanSphere.api import _, url_for, db, render_response
from pyClanSphere.models import AnonymousUser
from pyClanSphere.utils.admin import require_admin_privilege, \
     flash as admin_flash
from pyClanSphere.utils.http import redirect_to
from pyClanSphere.utils.pagination import AdminPagination
from pyClanSphere.utils.support import OrderedDict
from pyClanSphere.views.admin import render_admin_response, PER_PAGE

from pyClanSphere.plugins.bulletin_board.forms import CategoryForm, \
     DeleteCategoryForm, ForumForm, DeleteForumForm, PostForm, \
     DeletePostForm
from pyClanSphere.plugins.bulletin_board.models import *
from pyClanSphere.plugins.bulletin_board.privileges import BOARD_MANAGE

#
# Helper functions
#
def check_unread(user, topic, date=None):
    """Marks posts of given topic as read up until date if given"""

    if user is None:
        user = get_request().user
    if isinstance(user, AnonymousUser):
        return

    global_lastread = GlobalLastRead.query.get(user.id)
    if not global_lastread:
        GlobalLastRead(user)
        db.commit()
        return

    if global_lastread.date > topic.modification_date:
        return

    local_lastread = LocalLastRead.query.get((user.id,topic.id))
    if not local_lastread:
        LocalLastRead(user,topic,date)
        db.commit()
        return
    if local_lastread.date >= topic.modification_date:
        return

    local_lastread.date = date
    db.commit()
    return


#
# Frontend views
#

@cache.response(vary=('user',))
def board_index(request):
    """Render the board index page

    Available template variables:

        `categories`:
            Ordered Dictionary with 'catname': 'forums'

    :Template name: ``board_index.html``
    :URL endpoint: ``board/index``
    """
    renderdict = OrderedDict()
    categories = Category.query.order_by(db.asc('ordering')).all()
    for category in categories:
        forums = category.forums.order_by(db.asc('ordering')).all()
        if forums:
            user = request.user
            forumlist = [forum for forum in \
                         forums if forum.can_see(request.user)]
            if forumlist:
                renderdict[category] = forumlist

    return render_response('board_index.html', categories=renderdict)


@cache.response(vary=('user',))
def topic_list(request, forum_id, page=1):
    """Render topics for a given forum

    Available template variables:

        `forum`:
            Forum instance we give details about

        `pagination`:
            a pagination object to render a pagination

        `stickies`:
            Sorted list of sticky topics for given `forum_id`

        `topics`:
            Sorted list of non-sticky topics for given `forum_id`

        `form`:
            Form for topic creation or None if user is not allowed
            to create topics

    :Template name: ``board_topic_index.html``
    :URL endpoint: ``board/topics``
    """

    forum = Forum.query.get(forum_id)
    if forum is None:
        raise NotFound()
    if not forum.can_see(request.user):
       raise Forbidden()

    form = None
    if forum.can_create_topic(request.user):
        form = PostForm(forum)

    if request.method == 'POST':
        if form.validate(request.form):
            newpost = form.create_post()
            return redirect_to('board/topic_detail', topic_id=newpost.topic.id)

    data = Topic.query.filter(Topic.forum==forum) \
                .get_list('board/topics', page,
                          request.per_page, {'forum_id': forum_id})
    data['forum'] = forum
    data['form'] = form.as_widget() if form else None

    return render_response('board_topic_list.html', **data)


@cache.response(vary=('user',))
def topic_detail(request, topic_id, page=1):
    """Render posts for a given topic

    Available template variables:

        `topic`:
            Topic instance we give details about

        `pagination`:
            a pagination object to render a pagination

        `posts`:
            Sorted list of posts for given topic

        `form`:
            Form for new post creation or None if user is not allowed
            to post here

    :Template name: ``board_topic_detail.html``
    :URL endpoint: ``board/topic_detail``
    """

    topic = Topic.query.get(topic_id)
    if topic is None:
        raise NotFound()
    if not topic.can_see(request.user):
       raise Forbidden()

    form = None
    if topic.can_post(request.user):
        form = PostForm(topic)
        del form.title

    if request.method == 'POST':
        if form.validate(request.form):
            form.create_post()
            form.reset()

    data = Post.query.filter(Post.topic==topic)\
               .get_list('board/topic_detail', page,
                         request.per_page, {'topic_id': topic_id})

    # Mark read up to last shown post date
    check_unread(request.user, topic, data['posts'][-1].date)

    return render_response('board_topic_detail.html', topic=topic,
                          posts=data['posts'], pagination=data['pagination'],
                          form=form.as_widget() if form else None)


def topic_by_post(request, post_id):
    """This function acts as a proxy to find posts by id

    redirects to proper page if post is found, raise 404 otherwise
    :URL endpoint: ``board/post_find``
    """
    post = Post.query.get(post_id)
    if post is None:
        raise NotFound()
    postnr, page, topic_id = locate_post(post)
    return redirect_to('board/topic_detail', topic_id=topic_id, page=page, _anchor="post-%i" % (post_id,))


def post_edit(request, post_id):
    """Render post for editing, re-uses topic detail template

    Available template variables:

        `topic`:
            Topic instance we give details about

        `pagination`:
            a pagination object to render a pagination

        `posts`:
            Sorted list of posts for given topic

        `form`:
            Form for post editing

    :Template name: ``board_topic_detail.html``
    :URL endpoint: ``board/post_edit``
    """

    post = Post.query.get(post_id)
    if post is None:
        raise NotFound()
    (postnr, page, topic_id) = locate_post(post)

    user = request.user
    topic = post.topic
    if not topic.can_see(user) or not post.can_edit(user):
       raise Forbidden()

    form = PostForm(topic,post)
    del form.title

    if request.method == 'POST':
        if form.validate(request.form):
            form.save_changes(post)
            return redirect_to('board/post_find', post_id=post.id)

    data = Post.query.filter(Post.topic==topic)\
               .get_list('board/topic_detail', page,
                         request.per_page, {'topic_id': topic_id})

    return render_response('board_topic_detail.html', topic=topic,
                          posts=data['posts'], pagination=data['pagination'],
                          form=form.as_widget() if form else None)


def locate_post(searchpost, per_page=None):
    """Locate a post and return page and topic which it is on"""

    assert searchpost is not None
    topic = searchpost.topic
    posts = Post.query.filter(Post.topic==topic).order_by(db.asc(Post.date)).all()
    number = -1
    for postnr, post in enumerate(posts):
        if post.id == searchpost.id:
            number = postnr
            break
    if number == -1:
        raise get_application.InternalError('Post searching returned invalid id, check database consistency')

    page = 1
    if per_page:
        page = ceil(postnr/perpage)

    return (postnr, page, topic.id)


def post_delete(request, post_id):
    """Delete a post"""

    post = Post.query.get(post_id)
    if post is None:
        raise NotFound()
    (postnr, page, topic_id) = locate_post(post)

    user = request.user
    topic = post.topic
    if not post.can_delete(user):
       raise Forbidden()

    form = DeletePostForm(post)

    if request.method == 'POST':
        if form.validate(request.form):
            if 'confirm' in request.form:
                forum = topic.forum
            try:
                form.delete_post()
                return redirect_to('board/topic_detail', topic_id=topic.id)
            except TopicEmpty:
                return redirect_to('board/topics', forum_id=forum.id)
                
    return render_response('board_delete_post.html', topic=topic,
                          post=post, form=form.as_widget())
#
# Admin views
#

# Categories
endpointbase = 'admin/board/categories'
cat_endpoints = {
    'list': endpointbase,
    'delete': endpointbase + '/delete',
    'edit': endpointbase + '/edit',
}

@require_admin_privilege(BOARD_MANAGE)
def categories_list(request, page=1):
    """Show all categories in a list."""

    data = Category.query.get_list(cat_endpoints['list'], page,
                                   per_page=PER_PAGE,
                                   paginator=AdminPagination)

    return render_admin_response('admin/board_category_list.html', 'board.categories', **data)


@require_admin_privilege(BOARD_MANAGE)
def category_edit(request, category_id=None):
    """Edit an existing category or create a new one."""

    category = None
    if category_id is not None:
        category = Category.query.get(category_id)
        if category is None:
            raise NotFound()
    form = CategoryForm(category)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect(cat_endpoints['list'])
        elif 'delete' in request.form and category:
            return redirect_to(cat_endpoints['delete'], category_id=category_id)
        elif form.validate(request.form):
            if category is None:
                category = form.create_category()
                msg = _('Category %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes(category)
                msg = _('Category %s was updated successfully.')
                icon = 'info'

            admin_flash(msg % ('<a href="%s">%s</a>' % (url_for(cat_endpoints['edit'], category_id=category.id),
                               escape(category.name))), icon)

            if 'save_and_continue' in request.form:
                return redirect_to(cat_endpoints['edit'], category_id=category_id)
            elif 'save_and_new' in request.form:
                return redirect_to(cat_endpoints['edit'])
            return redirect_to(cat_endpoints['list'])
    return render_admin_response('admin/board_base_edit.html', 'board.categories',
                                 form=form.as_widget(), itemname=_('Category'))


@require_admin_privilege(BOARD_MANAGE)
def category_delete(request, category_id=None):
    category = Category.query.get(category_id)
    if category is None:
        raise NotFound()
    form = DeleteCategoryForm(category)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return redirect_to(cat_endpoints['edit'], category_id=category_id)
        if form.validate(request.form) and 'confirm' in request.form:
            msg = _('The category %s was deleted successfully.')  % \
                  escape(category.name)
            icon = 'remove'
            form.delete_category()
            admin_flash(msg, icon)
            return redirect_to(cat_endpoints['list'])

    return render_admin_response('admin/board_base_delete.html', 'board.categories',
                                 form=form.as_widget(), itemname=_('Category'),
                                 childitemnames=_('Forums'), entryname=category.name)

# Forums

endpointbase = 'admin/board/forums'
forum_endpoints = {
    'list': endpointbase,
    'delete': endpointbase + '/delete',
    'edit': endpointbase + '/edit',
}

@require_admin_privilege(BOARD_MANAGE)
def forum_list(request, page=1):
    """Show all forums in a grouped list."""

    # group this by category inside an OrderedDict, as we're sorted already 
    data = Forum.query.get_list(forum_endpoints['list'], page,
                                per_page=PER_PAGE,
                                paginator=AdminPagination)
    forumdict = OrderedDict()
    for forum in data['forums']:
        cat = forum.category.name
        if cat not in forumdict:
            forumdict[cat] = []
        forumdict[cat].append(forum)
    
    return render_admin_response('admin/board_forum_list.html', 'board.forums',
                                 forums=forumdict, pagination=data['pagination'])


@require_admin_privilege(BOARD_MANAGE)
def forum_edit(request, forum_id=None):
    """Edit an existing forum or create a new one."""

    forum = None
    if forum_id is not None:
        forum = Forum.query.get(forum_id)
        if forum is None:
            raise NotFound()
    form = ForumForm(forum)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect(forum_endpoints['list'])
        elif 'delete' in request.form and forum:
            return redirect_to(forum_endpoints['delete'], forum_id=forum_id)
        elif form.validate(request.form):
            if forum is None:
                forum = form.create_forum()
                msg = _('The forum %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes(forum)
                msg = _('The forum %s was updated successfully.')
                icon = 'info'

            admin_flash(msg % ('<a href="%s">%s</a>' % (url_for(forum_endpoints['edit'], forum_id=forum.id),
                               escape(forum.name))), icon)

            if 'save_and_continue' in request.form:
                return redirect_to(forum_endpoints['edit'], forum_id=forum_id)
            elif 'save_and_new' in request.form:
                return redirect_to(forum_endpoints['edit'])
            return redirect_to(forum_endpoints['list'])
    return render_admin_response('admin/board_base_edit.html', 'board.forums',
                                 form=form.as_widget(), itemname=_('Forum'))


@require_admin_privilege(BOARD_MANAGE)
def forum_delete(request, forum_id=None):
    forum = Forum.query.get(forum_id)
    if forum is None:
        raise NotFound()
    form = DeleteForumForm(forum)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return redirect_to(cat_endpoints['edit'], forum_id=forum_id)
        if form.validate(request.form) and 'confirm' in request.form:
            msg = _('The forum %s was deleted successfully.')  % \
                  escape(forum.name)
            icon = 'remove'
            form.delete_forum()
            admin_flash(msg, icon)
            return redirect_to(forum_endpoints['list'])

    return render_admin_response('admin/board_base_delete.html', 'board.forums',
                                 form=form.as_widget(), itemname=_('Forum'),
                                 childitemnames=_('Topics'), entryname=forum.name)
