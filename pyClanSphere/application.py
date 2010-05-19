# -*- coding: utf-8 -*-
"""
    pyClanSphere.application
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements the central application object :class:`pyClanSphere`
    and a couple of helper functions and classes.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import sys
from os import path, remove, makedirs, walk, environ
from time import time
from urlparse import urlparse
from collections import deque
from inspect import getdoc
from traceback import format_exception
from pprint import pprint
from StringIO import StringIO
from datetime import datetime, timedelta

from babel import Locale

from jinja2 import Environment, BaseLoader, TemplateNotFound, Markup

from sqlalchemy.exceptions import SQLAlchemyError

from werkzeug import Request as RequestBase, Response as ResponseBase, \
     SharedDataMiddleware, url_quote, routing, redirect as _redirect, \
     escape, cached_property, url_encode
from werkzeug.exceptions import HTTPException, Forbidden, \
     NotFound
from werkzeug.contrib.securecookie import SecureCookie

from pyClanSphere import _core, signals
from pyClanSphere.environment import SHARED_DATA, BUILTIN_TEMPLATE_PATH, \
     BUILTIN_PLUGIN_FOLDER
from pyClanSphere.database import db, cleanup_session
from pyClanSphere.cache import get_cache, result as cached_result, get_jinja_cache
from pyClanSphere.utils import ClosingIterator, local, local_manager, dump_json, \
     htmlhelpers
from pyClanSphere.utils.datastructures import ReadOnlyMultiMapping
from pyClanSphere.utils.exceptions import UserException

from pyClanSphere._ext.postmarkup import create as postmarkup_create
from pyClanSphere._ext.smiley import lib as smileys_lib

#: the default theme settings
DEFAULT_THEME_SETTINGS = {
    # pagination defaults
    'pagination.normal':            u'<a href="%(url)s">%(page)d</a>',
    'pagination.active':            u'<strong>%(page)d</strong>',
    'pagination.commata':           u'<span class="commata">,\n</span>',
    'pagination.ellipsis':          u'<span class="ellipsis"> …\n</span>',
    'pagination.threshold':         3,
    'pagination.left_threshold':    2,
    'pagination.right_threshold':   1,
    'pagination.prev_link':         False,
    'pagination.next_link':         False,
    'pagination.gray_prev_link':    True,
    'pagination.gray_next_link':    True,
    'pagination.simple':            False,

    # datetime formatting settings
    'date.date_format.default':     'medium',
    'date.datetime_format.default': 'medium',
    'date.date_format.short':       None,
    'date.date_format.medium':      None,
    'date.date_format.full':        None,
    'date.date_format.long':        None,
    'date.datetime_format.short':   None,
    'date.datetime_format.medium':  None,
    'date.datetime_format.full':    None,
    'date.datetime_format.long':    None,

    # reCAPTCHA theme choice may be overridden by theme
    'recaptcha.theme':              None,

    # query optimizations for overview pages.  Themes can change the
    # eager/lazy loading settings of some queries to remove unnecessary
    # overhead that is not in use for what they want to display.  For
    # example a theme that wants to load a headline-overview of all the
    # posts in a specific tag but no text at all it makes no sense to
    # load the text and more just to throw away the information.
    # for more information have a look at PostQuery.lightweight
    'sql.index.eager':              frozenset(),
    'sql.index.lazy':               frozenset(),
    'sql.index.deferred':           frozenset(),
}


def get_request():
    """Return the current request.  If no request is available this function
    returns `None`.
    """
    return getattr(local, 'request', None)

def get_application():
    """Get the application instance.  If the application was not yet set up
    the return value is `None`
    """
    return _core._application

def url_for(endpoint, **args):
    """Get the URL to an endpoint.  The keyword arguments provided are used
    as URL values.  Unknown URL values are used as keyword argument.
    Additionally there are some special keyword arguments:

    `_anchor`
        This string is used as URL anchor.

    `_external`
        If set to `True` the URL will be generated with the full server name
        and `http://` prefix.
    """
    if hasattr(endpoint, 'get_url_values'):
        rv = endpoint.get_url_values()
        if rv is not None:
            if isinstance(rv, basestring):
                return make_external_url(rv)
            endpoint, updated_args = rv
            args.update(updated_args)
    anchor = args.pop('_anchor', None)
    external = args.pop('_external', False)
    rv = get_application().url_adapter.build(endpoint, args,
                                             force_external=external)
    if anchor is not None:
        rv += '#' + url_quote(anchor)
    return rv

def shared_url(spec):
    """Returns a URL to a shared resource."""
    endpoint, filename = spec.split('::', 1)
    return url_for(endpoint + '/shared', filename=filename)

def add_link(rel, href, type, title=None, charset=None, media=None):
    """Add a new link to the metadata of the current page being processed."""
    local.page_metadata.append(('link', {
        'rel':      rel,
        'href':     href,
        'type':     type,
        'title':    title,
        'charset':  charset,
        'media':    media
    }))

def add_meta(http_equiv=None, name=None, content=None):
    """Add a new meta element to the metadata of the current page."""
    local.page_metadata.append(('meta', {
        'http_equiv':   http_equiv,
        'name':         name,
        'content':      content
    }))

def add_script(src, type='text/javascript'):
    """Load a script."""
    local.page_metadata.append(('script', {
        'src':      src,
        'type':     type
    }))


def add_header_snippet(html):
    """Add some HTML as header snippet."""
    local.page_metadata.append(('snippet', {
        'html':     html
    }))

def select_template(templates):
    """Selects the first template from a list of templates that exists."""
    env = get_application().template_env
    for template in templates:
        if template is not None:
            try:
                return env.get_template(template)
            except TemplateNotFound:
                pass
    raise TemplateNotFound('<multiple-choices>')

def render_template(template_name, _stream=False, **context):
    """Renders a template. If `_stream` is ``True`` the return value will be
    a Jinja template stream and not an unicode object.
    This is used by `render_response`.  If the `template_name` is a list of
    strings the first template that exists is selected.
    """
    if not isinstance(template_name, basestring):
        tmpl = select_template(template_name)
        template_name = tmpl.name
    else:
        tmpl = get_application().template_env.get_template(template_name)

    signals.before_render_template.send(template_name=template_name, stream=_stream, context=context)

    if _stream:
        return tmpl.stream(context)
    return tmpl.render(context)

def render_response(template_name, **context):
    """Like render_template but returns a response. If `_stream` is ``True``
    the response returned uses the Jinja stream processing. This is useful
    for pages with lazy generated content or huge output where you don't
    want the users to wait until the calculation ended. Use streaming only
    in those situations because it's usually slower than bunch processing.
    """
    return Response(render_template(template_name, **context))

class Theme(object):
    """Represents a theme and is created automatically by `add_theme`."""
    app = None

    def __init__(self, name, template_path, metadata=None,
                 settings=None, configuration_page=None):
        BaseLoader.__init__(self)
        self.name = name
        self.template_path = template_path
        self.metadata = metadata or {}
        self._settings = settings or {}
        self.configuration_page = configuration_page

    @property
    def configurable(self):
        return self.configuration_page is not None

    @property
    def preview_url(self):
        if self.metadata.get('preview'):
            return shared_url(self.metadata['preview'])

    @property
    def has_preview(self):
        return bool(self.metadata.get('preview'))

    @property
    def is_current(self):
        return self.name == self.app.cfg['theme']

    @property
    def display_name(self):
        return self.metadata.get('name') or self.name.title()

    @property
    def description(self):
        """Return the description of the theme."""
        return self.metadata.get('description', u'')

    @property
    def has_author(self):
        """Does the theme has an author at all?"""
        return 'author' in self.metadata

    @property
    def author_info(self):
        """The author, mail and author URL of the theme."""
        from pyClanSphere.utils.mail import split_email
        return split_email(self.metadata.get('author', u'Nobody')) + \
               (self.metadata.get('author_url'),)

    @property
    def html_author_info(self):
        """Return the author info as html link."""
        name, email, url = self.author_info
        if not url:
            if not email:
                return escape(name)
            url = 'mailto:%s' % url_quote(email)
        return u'<a href="%s">%s</a>' % (
            escape(url),
            escape(name)
        )

    @property
    def author(self):
        """Return the author of the plugin."""
        x = self.author_info
        return x[0] or x[1]

    @property
    def author_email(self):
        """Return the author email address of the theme."""
        return self.author_info[1]

    @property
    def author_url(self):
        """Return the URL of the author of the theme."""
        return self.author_info[2]

    @cached_property
    def settings(self):
        return ReadOnlyMultiMapping(self._settings, DEFAULT_THEME_SETTINGS)

    def get_url_values(self):
        if self.configurable:
            return self.name + '/configure', {}
        raise TypeError('can\'t link to unconfigurable theme')

    def get_source(self, name):
        parts = [x for x in name.split('/') if not x == '..']
        for fn in self.get_searchpath():
            fn = path.join(fn, *parts)
            if path.exists(fn):
                f = file(fn)
                try:
                    contents = f.read().decode('utf-8')
                finally:
                    f.close()
                mtime = path.getmtime(fn)
                return contents, fn, lambda: mtime == path.getmtime(fn)

    def get_overlay_path(self, template):
        """Return the path to an overlay for a template."""
        return path.join(self.app.instance_folder, 'overlays',
                         self.name, template)

    def overlay_exists(self, template):
        """Check if an overlay for a given template exists."""
        return path.exists(self.get_overlay_path(template))

    def get_overlay(self, template):
        """Return the source of an overlay."""
        f = file(self.get_overlay_path(template))
        try:
            lines = f.read().decode('utf-8', 'ignore').splitlines()
        finally:
            f.close()
        return u'\n'.join(lines)

    def set_overlay(self, template, data):
        """Set an overlay."""
        filename = self.get_overlay_path(template)
        try:
            makedirs(path.dirname(filename))
        except OSError:
            pass
        data = u'\n'.join(data.splitlines())
        if not data.endswith('\n'):
            data += '\n'
        f = file(filename, 'w')
        try:
            f.write(data.encode('utf-8'))
        finally:
            f.close()

    def remove_overlay(self, template, silent=False):
        """Remove an overlay."""
        try:
            remove(self.get_overlay_path(template))
        except OSError:
            if not silent:
                raise

    def get_searchpath(self):
        """Get the searchpath for this theme including plugins and
        all other template locations.
        """
        # before loading the normal template paths we check for overlays
        # in the instance overlay folder
        searchpath = [path.join(self.app.instance_folder, 'overlays',
                                self.name)]

        # if we have a real theme add the template path to the searchpath
        # on the highest position
        if self.name != 'default':
            searchpath.append(self.template_path)

        # add the template locations of the plugins
        searchpath.extend(self.app._template_searchpath)

        # now after the plugin searchpaths add the builtin one
        searchpath.append(BUILTIN_TEMPLATE_PATH)

        return searchpath

    def list_templates(self):
        """Return a sorted list of all templates."""
        templates = set()
        for p in self.get_searchpath():
            for dirpath, dirnames, filenames in walk(p):
                dirpath = dirpath[len(p) + 1:]
                if dirpath.startswith('.'):
                    continue
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                    templates.add(path.join(dirpath, filename).
                                  replace(path.sep, '/'))
        return sorted(templates)

    def format_datetime(self, datetime=None, format=None):
        """Datetime formatting for the template. The (`datetimeformat`
        filter)
        """
        format = self._get_babel_format('datetime', format)
        return i18n.format_datetime(datetime, format)

    def format_date(self, date=None, format=None):
        """Date formatting for the template.  (the `dateformat` filter)"""
        format = self._get_babel_format('date', format)
        return i18n.format_date(date, format)

    def _get_babel_format(self, key, format):
        """A small helper for the datetime formatting functions."""
        if format is None:
            format = self.settings['date.%s_format.default' % key]
        if format in ('short', 'medium', 'full', 'long'):
            rv = self.settings['date.%s_format.%s' % (key, format)]
            if rv is not None:
                format = rv
        return format


class ThemeLoader(BaseLoader):
    """Forwards theme lookups to the current active theme."""

    def __init__(self, app):
        BaseLoader.__init__(self)
        self.app = app

    def get_source(self, environment, name):
        rv = self.app.theme.get_source(name)
        if rv is None:
            raise TemplateNotFound(name)
        return rv


class InternalError(UserException):
    """Subclasses of this exception are used to signal internal errors that
    should not happen, but may do if the configuration is garbage.  If an
    internal error is raised during request handling they are converted into
    normal server errors for anonymous users (but not logged!!!), but if the
    current user is an administrator, the error is displayed.
    """

    help_text = None


class Request(RequestBase):
    """This class holds the incoming request data."""

    # Limit total upload filesize to 16 MB
    max_content_length = 1024 * 1024 * 16

    def __init__(self, environ, app=None):
        RequestBase.__init__(self, environ)
        self.queries = []
        if app is None:
            app = get_application()
        self.app = app

        engine = self.app.database_engine

        # get the session and try to get the user object for this request.
        from pyClanSphere.models import User
        user = None
        cookie_name = app.cfg['session_cookie_name']
        session = SecureCookie.load_cookie(self, cookie_name,
                                           app.secret_key)
        user_id = session.get('uid')
        if user_id:
            user = User.query.options(db.eagerload('groups'),
                                      db.eagerload('groups', '_privileges')) \
                             .get(user_id)
            now = datetime.utcnow()
            # mark user online, though only once a minute to not mess with
            # the database too much
            if not user.last_visited or \
                   ((now - user.last_visited) > timedelta(minutes=1)):
               user.last_visited = now
               db.commit()
        if user is None:
            user = User.query.get_nobody()
        self.user = user
        self.session = session
        self.per_page = None
        if 'per_page' in self.values:
            try:
                self.per_page = int(self.values['per_page'])
            except:
                pass

    @property
    def is_behind_proxy(self):
        """Are we behind a proxy?"""
        return environ.get('PYCLANSPHERE_BEHIND_PROXY') == '1'

    def login(self, user, permanent=False):
        """Log the given user in. Can be user_id, username or
        a full blown user object.
        """
        from pyClanSphere.models import User
        if isinstance(user, (int, long)):
            user = User.query.get(user)
        elif isinstance(user, basestring):
            user = User.query.filter_by(username=user).first()
        if user is None:
            raise RuntimeError('User does not exist')
        self.user = user
        signals.user_logged_in.send(user=user)
        self.session['uid'] = user.id
        self.session['lt'] = time()
        if permanent:
            self.session['pmt'] = True

    def logout(self):
        """Log the current user out."""
        current_user = self.user
        signals.before_user_logout.send(user=current_user)
        from pyClanSphere.models import User
        user = self.user
        self.user = User.query.get_nobody()
        self.session.clear()
        signals.after_user_logout.send(user=current_user)


class Response(ResponseBase):
    """This class holds the resonse data.  The default charset is utf-8
    and the default mimetype ``'text/html'``.
    """
    default_mimetype = 'text/html'


class pyClanSphere(object):
    """The central application object.

    Even though the :class:`pyClanSphere` class is a regular Python class, you can't
    create instances by using the regular constructor.  The only documented way
    to create this class is the :func:`pyClanSphere._core.setup` function or by
    using one of the dispatchers created by :func:`pyClanSphere._core.get_wsgi_app`.
    """

    _setup_only = []
    def setuponly(f, container=_setup_only):
        """Mark a function as "setup only".  After the setup those
        functions will be replaced with a dummy function that raises
        an exception."""
        container.append(f.__name__)
        f.__doc__ = (getdoc(f) or '') + '\n\n*This function can only be ' \
                    'called during application setup*'
        return f

    def __init__(self, instance_folder):
        # this check ensures that only setup() can create pyClanSphere instances
        if get_application() is not self:
            raise TypeError('cannot create %r instances. use the '
                            'pyClanSphere._core.setup() factory function.' %
                            self.__class__.__name__)
        self.instance_folder = path.abspath(instance_folder)

        # create the event manager, this is the first thing we have to
        # do because it could happen that events are sent during setup
        self.initialized = False

        # and instanciate the configuration. this won't fail,
        # even if the database is not connected.
        from pyClanSphere.config import Configuration
        self.cfg = Configuration(path.join(instance_folder, 'pyClanSphere.ini'))
        if not self.cfg.exists:
            raise _core.InstanceNotInitialized()

        # and hook in the logger
        self.log = log.Logger(path.join(instance_folder, self.cfg['log_file']),
                              self.cfg['log_level'])

        # the iid of the application
        self.iid = self.cfg['iid'].encode('utf-8')
        if not self.iid:
            self.iid = '%x' % id(self)

        # connect to the database
        self.database_engine = db.create_engine(self.cfg['database_uri'],
                                                self.instance_folder,
                                                self.cfg['database_debug'])

        # now setup the cache system
        self.cache = get_cache(self)

        # setup core package urls and shared stuff
        import pyClanSphere
        from pyClanSphere.urls import make_urls
        from pyClanSphere.views import all_views, \
             admin_content_type_handlers, absolute_url_handlers
        from pyClanSphere.services import all_services
        self.views = all_views.copy()
        self.admin_content_type_handlers = admin_content_type_handlers.copy()
        self._url_rules = make_urls(self)
        self._absolute_url_handlers = absolute_url_handlers[:]
        self._services = all_services.copy()
        self._shared_exports = {}
        self._template_globals = {}
        self._template_filters = {}
        self._template_tests = {}
        self._template_searchpath = []

        # initialize i18n/l10n system
        self.locale = Locale(self.cfg['language'])
        self.translations = i18n.load_core_translations(self.locale)

        # init themes
        _ = i18n.gettext
        default_theme = Theme('default', BUILTIN_TEMPLATE_PATH, {
            'name':         _(u'Default Theme'),
            'description':  _(u'Simple default theme that doesn\'t '
                              'contain any style information.'),
            'preview':      'core::default_preview.png'
        })
        default_theme.app = self
        self.themes = {'default': default_theme}

        self.apis = {}

        # the notification manager
        from pyClanSphere.notifications import NotificationManager, \
             DEFAULT_NOTIFICATION_SYSTEMS, DEFAULT_NOTIFICATION_TYPES

        self.notification_manager = NotificationManager()
        for system in DEFAULT_NOTIFICATION_SYSTEMS:
            self.add_notification_system(system)
        self.notification_types = DEFAULT_NOTIFICATION_TYPES.copy()

        # register the default privileges
        from pyClanSphere.privileges import DEFAULT_PRIVILEGES
        self.privileges = DEFAULT_PRIVILEGES.copy()

        # insert list of widgets
        from pyClanSphere.widgets import all_widgets
        self.widgets = dict((x.name, x) for x in all_widgets)

        # add searchpath for plugins
        from pyClanSphere.pluginsystem import find_plugins, set_plugin_searchpath
        self.plugin_folder = path.join(instance_folder, 'plugins')
        self.plugin_searchpath = [self.plugin_folder]
        for folder in self.cfg['plugin_searchpath']:
            folder = folder.strip()
            if folder:
                self.plugin_searchpath.append(
                    path.join(self.instance_folder, folder))
        self.plugin_searchpath.append(BUILTIN_PLUGIN_FOLDER)
        set_plugin_searchpath(self.plugin_searchpath)

        # load the plugins
        self.plugins = {}
        for plugin in find_plugins(self):
            if plugin.active:
                plugin.setup()
                self.translations.merge(plugin.translations)
            self.plugins[plugin.name] = plugin

        # set the active theme based on the config.
        theme = self.cfg['theme']
        if theme not in self.themes:
            log.warning(_(u'Theme “%s” is no longer available, falling back '
                          u'to default theme.') % theme, 'core')
            theme = 'default'
            self.cfg.change_single('theme', theme)
        self.theme = self.themes[theme]

        # init the template system with the core stuff
        from pyClanSphere import models

        env = Environment(loader=ThemeLoader(self), bytecode_cache=get_jinja_cache(self),
                          extensions=['jinja2.ext.i18n'], autoescape=True)
        env.globals.update(
            cfg=self.cfg,
            theme=self.theme,
            h=htmlhelpers,
            url_for=url_for,
            signals=signals,
            shared_url=shared_url,
            request=local('request'),
            render_widgets=lambda x=[]: Markup(render_template('_widgets.html', widgetoptions=x)),
            get_page_metadata=self.get_page_metadata,
            widgets=self.widgets,
            pyClanSphere={
                'version':      pyClanSphere.__version__,
                'copyright':    _(u'Copyright %(years)s by the pyClanSphere Team')
                                % {'years': '2009'}
            }
        )

        env.filters.update(
            json=dump_json,
            datetimeformat=self.theme.format_datetime,
            dateformat=self.theme.format_date,
            monthformat=i18n.format_month,
            fancydatetimeformat=i18n.format_fancydatetime,
            timedeltaformat=i18n.format_timedelta
        )

        env.install_gettext_translations(self.translations)

        # set up plugin template extensions
        env.globals.update(self._template_globals)
        env.filters.update(self._template_filters)
        env.tests.update(self._template_tests)
        del self._template_globals, self._template_filters, \
            self._template_tests
        self.template_env = env

        # now add the middleware for static file serving
        self.add_shared_exports('core', SHARED_DATA)
        self.add_middleware(SharedDataMiddleware, self._shared_exports)

        # set up the urls
        self.url_map = routing.Map(self._url_rules)
        del self._url_rules

        # and create a url adapter
        scheme, netloc, script_name = urlparse(self.cfg['site_url'])[:3]
        self.url_adapter = self.url_map.bind(netloc, script_name,
                                             url_scheme=scheme)

        # mark the app as finished and override the setup functions
        def _error(*args, **kwargs):
            raise RuntimeError('Cannot register new callbacks after '
                               'application setup phase.')
        self.__dict__.update(dict.fromkeys(self._setup_only, _error))

        self.initialized = True

        # init smileys
        smiley_parser = smileys_lib(path.join(SHARED_DATA,'smilies'),url_for('core/shared', filename='smilies/'))

        # init bbcode
        bbcode_parser = postmarkup_create(use_pygments=False)

        signals.after_bbcode_initialized.send(bbcode_parser=bbcode_parser)

        @cached_result('prettified_')
        def prettify(text):
            """Pass text through bbcode and smiley to make it look pretty to the user

            Later on this should be chosen by template and/or user

            Note: we don't use cached_property as the text varies. So store it in a system
                  cache if we have any.
                  The key for the cache is prettified_ and a hash of the text we want to prettify
            """

            if text is None:
                return Markup(u'')
            text = bbcode_parser(text)
            text = smiley_parser.makehappy(text)
            return Markup(text)

        env.filters.update(
            smileys=lambda x: Markup(smiley_parser.makehappy(x)),
            bbcode=lambda x: Markup(bbcode_parser(x)),
            prettify=prettify
        )

        env.globals.update(
            smileylist = lambda x: smiley_parser.get_panel(x)
        )

        #! called after the application and all plugins are initialized
        signals.application_setup_done.send()

    @property
    def wants_reload(self):
        """True if the application requires a reload.  This is `True` if
        the config was changed on the file system.  A dispatcher checks this
        value every request and automatically unloads and reloads the
        application if necessary.
        """
        return self.cfg.changed_external

    @property
    def secret_key(self):
        """Returns the secret key for the instance (binary!)"""
        return self.cfg['secret_key'].encode('utf-8')

    @setuponly
    def add_template_filter(self, name, callback):
        """Add a Jinja2 template filter."""
        self._template_filters[name] = callback

    @setuponly
    def add_template_test(self, name, callback):
        """Add a Jinja2 template test."""
        self._template_tests[name] = callback

    @setuponly
    def add_template_global(self, name, value):
        """Add a template global.  Object's added that way are available in
        the global template namespace.
        """
        self._template_globals[name] = value

    @setuponly
    def add_template_searchpath(self, path):
        """Add a new template searchpath to the application.  This searchpath
        is queried *after* the themes but *before* the builtin templates are
        looked up.
        """
        self._template_searchpath.append(path)

    @setuponly
    def add_api(self, name, preferred, callback, clan_id=1, url_key=None):
        """Add a new API to the site.  The newly added API is available at
        ``/_services/<name>`` and automatically exported in the RSD file.
        The `clan_id` is an unused oddity of the RSD file, preferred an
        indicator if this API is preferred or not.
        The callback is called for all requests to the service URL.
        """
        endpoint = 'services/' + name
        self.apis[name] = (clan_id, preferred, endpoint)
        if url_key is None:
            url_key = name.lower()
        url = '/_services/' + url_key
        self.add_url_rule(url, endpoint=endpoint)
        self.add_view(endpoint, callback)
        return url

    @setuponly
    def add_theme(self, name, template_path=None, metadata=None,
                  settings=None, configuration_page=None):
        """Add a theme. You have to provide the shortname for the theme
        which will be used in the admin panel etc. Then you have to provide
        the path for the templates. Usually this path is relative to the
        directory of the plugin's `__file__`.

        The metadata can be ommited but in that case some information in
        the admin panel is not available.

        Alternatively a custom :class:`Theme` object can be passed to this
        function as only argument.  This makes it possible to register
        custom theme subclasses too.
        """
        if isinstance(name, Theme):
            if template_path is not metadata is not settings \
               is not configuration_page is not None:
                raise TypeError('if a theme instance is provided extra '
                                'arguments must be ommited or None.')
            theme = name
        else:
            theme = Theme(name, template_path, metadata,
                          settings, configuration_page)
        if theme.app is not None:
            raise TypeError('theme is already registered to an application.')
        theme.app = self
        self.themes[theme.name] = theme

    @setuponly
    def add_shared_exports(self, name, path):
        """Add a shared export for name that points to a given path and
        creates an url rule for <name>/shared that takes a filename
        parameter.  A shared export is some sort of static data from a
        plugin.  Per default pyClanSphere will shared the data on it's own but
        in the future it would be possible to generate an Apache/nginx
        config on the fly for the static data.

        The static data is available at `/_shared/<name>` and points to
        `path` on the file system.  This also generates a URL rule named
        `<name>/shared` that accepts a `filename` parameter.  This can be
        used for URL generation.
        """
        self._shared_exports['/_shared/' + name] = path
        self.add_url_rule('/_shared/%s/<string:filename>' % name,
                          endpoint=name + '/shared', build_only=True)

    @setuponly
    def add_middleware(self, middleware_factory, *args, **kwargs):
        """Add a middleware to the application.  The `middleware_factory`
        is a callable that is called with the active WSGI application as
        first argument, `args` as extra positional arguments and `kwargs`
        as keyword arguments.

        The newly applied middleware wraps an internal WSGI application.
        """
        self.dispatch_wsgi = middleware_factory(self.dispatch_wsgi,
                                                   *args, **kwargs)

    @setuponly
    def add_config_var(self, key, field):
        """Add a configuration variable to the application.  The config
        variable should be named ``<plugin_name>/<variable_name>``.  The
        `variable_name` itself must not contain another slash.  Variables
        that are not prefixed are reserved for pyClanSphere' internal usage.
        The `field` is an instance of a field class from pyClanSphere.utils.forms
        that is used to validate the variable. It has to contain the default
        value for that variable.

        Example usage::

            app.add_config_var('my_plugin/my_var', BooleanField(default=True))
        """
        if key.count('/') > 1:
            raise ValueError('key might not have more than one slash')
        self.cfg.config_vars[key] = field

    @setuponly
    def add_url_rule(self, rule, **kwargs):
        """Add a new URL rule to the url map.  This function accepts the same
        arguments as a werkzeug routing rule.  Additionally a `prefix`
        parameter is accepted that can be used to add the common prefixes
        based on the configuration.  Basically the following two calls
        do exactly the same::

            app.add_url_rule('/foo', prefix='admin', ...)
            app.add_url_rule(app.cfg['admin_url_prefix'] + '/foo', ...)

        It also takes a `view` keyword argument that, if given registers
        a view for the url view::

            app.add_url_rule(..., endpoint='bar', view=bar)

        is equivalent to::

            app.add_url_rule(..., endpoint='bar')
            app.add_view('bar', bar)
        """
        prefix = kwargs.pop('prefix', None)
        if prefix is not None:
            rule = self.cfg[prefix + '_url_prefix'] + rule
        view = kwargs.pop('view', None)
        self._url_rules.append(routing.Rule(rule, **kwargs))
        if view is not None:
            self.views[kwargs['endpoint']] = view

    @setuponly
    def add_absolute_url(self, handler):
        """Adds a new callback as handler for absolute URLs.  If the normal
        request handling was unable to find a proper response for the request
        the handler is called with the current request as argument and can
        return a response that is then used as normal response.

        If a handler doesn't want to handle the response it may raise a
        `NotFound` exception or return `None`.

        This is for example used to implement the pages support in pyClanSphere.
        """
        self._absolute_url_handlers.append(handler)

    @setuponly
    def add_view(self, endpoint, callback):
        """Add a callback as view.  The endpoint is the endpoint for the URL
        rule and has to be equivalent to the endpoint passed to
        :meth:`add_url_rule`.
        """
        self.views[endpoint] = callback

    @setuponly
    def add_content_type(self, content_type, callback, admin_callbacks=None,
                         create_privilege=None, edit_own_privilege=None,
                         edit_other_privilege=None):
        """Register a view handler for a content type."""
        self.content_type_handlers[content_type] = callback
        if admin_callbacks is not None:
            self.admin_content_type_handlers[content_type] = admin_callbacks
        self.content_type_privileges[content_type] = (
            create_privilege,
            edit_own_privilege,
            edit_other_privilege
        )

    @setuponly
    def add_widget(self, widget):
        """Add a widget."""
        self.widgets[widget.name] = widget

    @setuponly
    def add_servicepoint(self, identifier, callback):
        """Add a new function as servicepoint.  A service point is a function
        that is called by an external non-human interface such as an
        JavaScript or XMLRPC client.  It's automatically exposed to all
        service interfaces.
        """
        self._services[identifier] = callback

    @setuponly
    def add_privilege(self, privilege):
        """Registers a new privilege."""
        self.privileges[privilege.name] = privilege

    @setuponly
    def add_notification_system(self, system):
        """Add the notification system to the list of notification systems
        the NotificationManager holds.
        """
        self.notification_manager.systems[system.key] = system(self)

    @setuponly
    def add_notification_type(self, type):
        """Registers a new notification type on the instance."""
        self.notification_manager.add_notification_type(type)

    def list_privileges(self):
        """Return a sorted list of privileges."""
        # TODO: somehow add grouping...
        result = [(x.name, unicode(x.explanation)) for x in
                  self.privileges.values()]
        result.sort(key=lambda x: x[0] == 'CLAN_ADMIN' or x[1].lower())
        return result

    def get_page_metadata(self):
        """Return the metadata as HTML part for templates.  This is normally
        called by the layout template to get the metadata for the head section.
        """
        from pyClanSphere.utils import dump_json
        generators = {'script': htmlhelpers.script, 'meta': htmlhelpers.meta,
                      'link': htmlhelpers.link, 'snippet': lambda html: html}
        result = [
            htmlhelpers.meta(name='generator', content='pyClanSphere'),
            htmlhelpers.link('EditURI', url_for('core/service_rsd'),
                             type='application/rsd+xml', title='RSD'),
            htmlhelpers.script(url_for('core/shared', filename='js/jQuery.js')),
            htmlhelpers.script(url_for('core/shared', filename='js/tiny_mce/jquery.tinymce.js')),
            htmlhelpers.script(url_for('core/shared', filename='js/pyClanSphere.js')),
            htmlhelpers.script(url_for('core/serve_translations'))
        ]

        # the url information.  Only expose the admin url for admin users
        # or calls to this method without a request.
        base_url = self.cfg['site_url'].rstrip('/')
        request = get_request()
        javascript = [
            'pyClanSphere.ROOT_URL = %s' % dump_json(base_url)
        ]
        if request is None or request.user.is_manager:
            javascript.append('pyClanSphere.ADMIN_URL = %s' %
                              dump_json(base_url + self.cfg['admin_url_prefix']))
        result.append(u'<script type="text/javascript">%s;</script>' %
                      '; '.join(javascript))

        for type, attr in local.page_metadata:
            result.append(generators[type](**attr))

        signals.before_metadata_assembled.send(result=result)
        return Markup(u'\n'.join(result))

    def handle_not_found(self, request, exception):
        """Handle a not found exception.  This also dispatches to plugins
        that listen for for absolute urls.  See `add_absolute_url` for
        details.
        """
        for handler in self._absolute_url_handlers:
            try:
                rv = handler(request)
                if rv is not None:
                    return rv
            except NotFound:
                # a not found exception has the same effect as returning
                # None.  The next handler is processed.  All other http
                # exceptions are passed trough.
                pass
        response = render_response('404.html')
        response.status_code = 404
        return response

    def send_error_notification(self, request, error):
        from pyClanSphere.notifications import send_notification_template, PYCLANSPHERE_ERROR
        request_buffer = StringIO()
        pprint(request.__dict__, request_buffer)
        request_buffer.seek(0)
        send_notification_template(
            PYCLANSPHERE_ERROR, 'notifications/on_server_error.zeml',
            user=request.user, summary=error.message,
            request_details=request_buffer.read(),
            longtext=''.join(format_exception(*sys.exc_info()))
        )

    def handle_server_error(self, request, exc_info=None, suppress_log=False):
        """Called if a server error happens.  Logs the error and returns a
        response with an error message.
        """
        if not suppress_log:
            log.exception('Exception happened at "%s"' % request.path,
                          'core', exc_info)
        response = render_response('500.html')
        response.status_code = 500
        return response

    def handle_internal_error(self, request, error, suppress_log=True):
        """Called if internal errors are caught."""
        if request.user.is_admin:
            response = render_response('internal_error.html', error=error)
            response.status_code = 500
            return response
        # We got here, meaning no admin has seen this error yet. Notify Them!
        self.send_error_notification(request, error)
        return self.handle_server_error(request, suppress_log=suppress_log)

    def dispatch_request(self, request):
        #! the after-request-setup event can return a response
        #! or modify the request object in place. If we have a
        #! response we just send it, no other modifications are done.
        for callback in signals.after_request_setup.receivers_for(signals.ANY):
            result = callback(request)
            if result is not None:
                return result

        # normal request dispatching
        try:
            try:
                endpoint, args = self.url_adapter.match(request.path)
                response = self.views[endpoint](request, **args)
            except NotFound, e:
                response = self.handle_not_found(request, e)
            except Forbidden, e:
                if request.user.is_somebody:
                    response = render_response('403.html')
                    response.status_code = 403
                else:
                    response = _redirect(url_for('account/login',
                                                 next=request.path))
        except HTTPException, e:
            response = e.get_response(request)
        except SQLAlchemyError, e:
            # Some database screwup?! Don't let pyClanSphere stay dispatching 500's
            # Also don't raise if the rollback causes another headache
            try:
                db.session.rollback()
            except:
                pass
            response = self.handle_internal_error(request, e,
                                                  suppress_log=False)

        # in debug mode on HTML responses we inject the collected queries.
        if self.cfg['database_debug'] and \
           getattr(response, 'mimetype', None) == 'text/html' and \
           isinstance(response.response, (list, tuple)):
            from pyClanSphere.utils.debug import inject_query_info
            inject_query_info(request, response)

        return response

    def dispatch_wsgi(self, environ, start_response):
        """This method is the internal WSGI request and is overridden by
        middlewares applied with :meth:`add_middleware`.  It handles the
        actual request dispatching.
        """
        # Create a new request object, register it with the application
        # and all the other stuff on the current thread but initialize
        # it afterwards.  We do this so that the request object can query
        # the database in the initialization method.
        request = object.__new__(Request)
        local.request = request
        local.page_metadata = []
        local.request_locals = {}
        try:
            request.__init__(environ, self)
        except Exception, e:
            if self.cfg['passthrough_errors']:
                raise
            if isinstance(e, SQLAlchemyError):
                # Chances our db has gone away, thus just clean the session and start over
                try:
                    # let's try to at least issue a rollback
                    db.session.rollback()
                except:
                    pass
                log.warning(u'SQL Database was unable to assign user to request during init, retrying with fresh session. Play with pool_recycle to get rid of this')
                # as unsaved data will be lost at this state anyway, clear 
                db.session.remove()
                try:
                    request.__init__(environ, self)
                except:
                    # Bad luck, so present error
                    return self.handle_server_error(local.request)(environ, start_response)
            else:
                return self.handle_server_error(local.request)(environ, start_response)

        # check if the site is in maintenance_mode and the user is
        # not an administrator. in that case just show a message that
        # the user is not privileged to view the site right now. Exception:
        # the page is the login page for the site.
        # XXX: Remove 'admin_prefix' references for pyClanSphere 0.3
        #      It still exists because some themes might depend on it.
        js_translations = url_for('core/serve_translations')
        admin_prefix = self.cfg['admin_url_prefix']
        account_prefix = self.cfg['account_url_prefix']
        if self.cfg['maintenance_mode'] and \
           request.path not in (account_prefix, admin_prefix, js_translations) \
           and not (request.path.startswith(admin_prefix + '/') or
                    request.path.startswith(account_prefix + '/')):
            if not request.user.has_privilege(
                                        self.privileges['ENTER_ADMIN_PANEL']):
                response = render_response('maintenance.html')
                response.status_code = 503
                return response(environ, start_response)

        # if HTTPS enforcement is active, we redirect to HTTPS if
        # possibile without problems (no playload)
        if self.cfg['force_https'] and request.method in ('GET', 'HEAD') and \
           environ['wsgi.url_scheme'] == 'http':
            response = _redirect('https' + request.url[4:], 301)
            return response(environ, start_response)

        # wrap the real dispatching in a try/except so that we can
        # intercept exceptions that happen in the application.
        try:
            response = self.dispatch_request(request)

            # make sure the response object is one of ours
            response = Response.force_type(response, environ)

            #! allow plugins to change the response object
            for callback in signals.before_response_processed.receivers_for(signals.ANY):
                result = callback(response)
                if result is not None:
                    response = result
        except InternalError, e:
            response = self.handle_internal_error(request, e)
        except:
            if self.cfg['passthrough_errors']:
                raise
            response = self.handle_server_error(request)

        # update the session cookie at the request end if the
        # session data requires an update.
        if request.session.should_save:
            # set the secret key explicitly at the end of the request
            # to not log out the administrator if he changes the secret
            # key in the config editor.
            request.session.secret_key = self.secret_key
            cookie_name = self.cfg['session_cookie_name']
            if request.session.get('pmt'):
                max_age = 60 * 60 * 24 * 31
                expires = time() + max_age
            else:
                max_age = expires = None
            request.session.save_cookie(response, cookie_name, max_age=max_age,
                                        expires=expires, session_expires=expires)

        return response(environ, start_response)

    def perform_subrequest(self, path, query=None, method='GET', data=None,
                           timeout=None, response_wrapper=Response):
        """Perform an internal subrequest against pyClanSphere.  This method spawns a
        separate thread and lets an internal WSGI client answer the request.
        The return value is then converted into a pyClanSphere response object and
        returned.

        A separate thread is spawned so that the internal request does not
        caused troubles for the current one in terms of persistent database
        objects.

        This is for example used in the `open_url` method to allow access to
        site local resources without dead-locking if the WSGI server does not
        support concurrency (single threaded and just one process for example).
        """
        from werkzeug import Client
        from threading import Event, Thread
        event = Event()
        response = []
        input_stream = None
        if hasattr(data, 'read'):
            input_stream = data
            data = None

        def make_request():
            try:
                client = Client(self, response_wrapper)
                response.append(client.open(path, self.cfg['site_url'],
                                            method=method, data=data,
                                            query_string=url_encode(query),
                                            input_stream=input_stream))
            except:
                response.append(sys.exc_info())
            event.set()

        Thread(target=make_request).start()
        event.wait(timeout)
        if not response:
            raise NetException('Timeout on internal subrequest')
        if isinstance(response[0], tuple):
            exc_type, exc_value, tb = response[0]
            raise exc_type, exc_value, tb
        return response[0]

    def __call__(self, environ, start_response):
        """Make the application object a WSGI application."""
        return ClosingIterator(self.dispatch_wsgi(environ, start_response),
                               [local_manager.cleanup, cleanup_session])

    def __repr__(self):
        return '<pyClanSphere %r [%s]>' % (
            self.instance_folder,
            self.iid
        )

    # remove our decorator
    del setuponly

# import here because of circular dependencies
from pyClanSphere import i18n
from pyClanSphere.utils import log
from pyClanSphere.utils.http import make_external_url
