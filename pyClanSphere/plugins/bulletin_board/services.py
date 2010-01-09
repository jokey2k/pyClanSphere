# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements JSON API for the board module.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug import abort

from pyClanSphere.plugins.bulletin_board.models import *

def do_get_post(req):
    post_id = req.values.get('post_id')
    if post_id is None:
        abort(404)
    post = Post.query.get(post_id)
    if post is None:
        abort(404)
    topic = post.topic
    if not topic.can_see(req.user):
       abort(403)
    return {
        'id':           post.id,
        'author':       post.author_str,
        'topic_id':     topic.id,
        'text':         unicode(post.text),
        'date':         int(post.date.strftime('%s')),
    }
