Caching
=======

Caching backends are inherited from :mod:`werkzeug`, basically just
wrappers around get, set and clear methods.

Implemented caching backends
----------------------------

Simple Cache
~~~~~~~~~~~~

The simple cache is a very basic memory cache inside the server
process. This cache works only if you have a persistent environment.
Roughly speaking this cache works better the higher the number of threads
in a process and the lower the number of processes. If you have the chance
to use a memcached, you should not use the simple cache.

Filesystem
~~~~~~~~~~

This cache system stores the cache information on the filesystem. If IO
is a problem for you, you should not use this cache. However for most
of the cases the filesystem it should be fast enough.

Memcached
~~~~~~~~~

This cache system uses one or multiple remote memcached servers for
storing the cache information. It requires at least one running memcached
daemon. This is useful for high traffic sites.

Exposed API
-----------

You can simply decorate your function with either
:meth:`pyClanSphere.cache.result` like this ::

    @cache.result('prettified_')
    def prettify(text):
        if text is None:
            return Markup(u'')
        text = bbcode_parser(text)
        text = smiley_parser.makehappy(text)
        return Markup(text)


or cache the whole view function by decorating with
:meth:`pyClanSphere.cache.result` instead. ::

    @cache.response(vary=('user',))
    def index(req, page=1):
        data = News.query.published() \
                   .get_list(endpoint='news/index', page=page)

        return render_response('news_index.html', **data)

Normally you don't need to touch the other functions. Also this is
exposed through the asterisk import of :mod:`pyClanSphere.api`


.. automodule:: pyClanSphere.cache
   :members:
