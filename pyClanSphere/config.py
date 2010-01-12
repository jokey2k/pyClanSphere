# -*- coding: utf-8 -*-
"""
    pyClanSphere.config
    ~~~~~~~~~~~~~~~~~~~

    This module implements the configuration.  The configuration is a more or
    less flat thing saved as ini in the instance folder.  If the configuration
    changes the application is reloaded automatically.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
from os import path
from threading import Lock

from pyClanSphere import environment
from pyClanSphere.i18n import lazy_gettext, _, list_timezones, list_languages
from pyClanSphere.utils import log
from pyClanSphere.utils.forms import TextField, IntegerField, BooleanField, \
    ChoiceField, CommaSeparated
from pyClanSphere.utils.validators import ValidationError, is_valid_url_prefix, \
    is_valid_url_format, is_netaddr, is_valid_email
from pyClanSphere.application import InternalError


_dev_mode = environment.MODE == 'development'

l_ = lazy_gettext

#: variables the pyClanSphere core uses
DEFAULT_VARS = {
    # core system settings
    'database_uri':             TextField(default=u'', help_text=l_(
        u'The database URI.  For more information about database settings '
        u'consult the pyClanSphere help.')),
    'force_https':              BooleanField(default=False, help_text=l_(
        u'If a request to an http URL comes in, pyClanSphere will redirect to the same '
        u'URL on https if this is savely possible.  This requires a working '
        u'SSL setup or otherwise pyClanSphere will become unresponsive.')),
    'database_debug':           BooleanField(default=False, help_text=l_(
        u'If enabled, the database will collect the SQL statements and add '
        u'them to the bottom of the page for easier debugging')),
    'clan_title':               TextField(default=l_(u'My Clan Page')),
    'clan_tagline':             TextField(default=l_(u'just another Clan page')),
    'site_url':                 TextField(default=u'', help_text=l_(
        u'The base URL of the site.  This has to be set to a full canonical URL '
        u'(including http or https).  If not set, the application will behave '
        u'confusingly.  Remember to change this value if you move your site '
        u'to a new location.')),
    'clan_email':               TextField(default=u'', help_text=l_(
        u'The email address given here is used by the notification system to send '
        u'emails from.  Also plugins that send mails will use this address as '
        u'the sender address.'), validators=[is_valid_email()]),
    'timezone':                 ChoiceField(choices=sorted(list_timezones()),
        default=u'UTC', help_text=l_(
        u'The timezone of the site.  All times and dates in the user interface '
        u'and on the website will be shown in this timezone.  It\'s save to '
        u'change the timezone after posts are created because the information '
        u'in the database is stored as UTC.')),
    'maintenance_mode':         BooleanField(default=False, help_text=l_(
        u'If set to true, the site enables the maintainance mode.')),
    'session_cookie_name':      TextField(default=u'pyClanSphere_session',
        help_text=l_(u'If there are multiple pyClanSphere installations on '
        u'the same host the cookie name should be set to something different '
        u'for each one.')),
    'theme':                    TextField(default=u'default'),
    'secret_key':               TextField(default=u'', help_text=l_(
        u'The secret key is used for various security related tasks in the '
        u'system. For example, the cookie is signed with this value.')),
    'language':                 ChoiceField(choices=list_languages(False),
                                            default=u'en'),

    'iid':                      TextField(default=u'', help_text=l_(
        u'The iid uniquely identifies the pyClanSphere instance.  Currently this '
        u'value is unused, but once set you should not modify it.')),

    # log and development settings
    'log_file':                 TextField(default=u'pyClanSphere.log'),
    'log_level':                ChoiceField(choices=[(k, l_(k)) for k, v
                                                in sorted(log.LEVELS.items(),
                                                          key=lambda x: x[1])],
                                            default=u'warning'),
    'log_email_only':           BooleanField(default=_dev_mode,
        help_text=l_(u'During development activating this is helpful to '
        u'log emails into a mail.log file in your instance folder instead '
        u'of delivering them to your MTA.')),
    'passthrough_errors':       BooleanField(default=_dev_mode,
        help_text=l_(u'If this is set to true, errors in pyClanSphere '
        u'are not caught so that debuggers can catch it instead.  This is '
        u'useful for plugin and core development.')),

    # url settings
    'account_url_prefix':       TextField(default=u'/account',
                                          validators=[is_valid_url_prefix()]),
    'admin_url_prefix':         TextField(default=u'/admin',
                                          validators=[is_valid_url_prefix()]),

    # cache settings
    'enable_eager_caching':     BooleanField(default=False),
    'cache_timeout':            IntegerField(default=300, min_value=10),
    'cache_system':             ChoiceField(choices=[
        (u'null', l_(u'No Cache')),
        (u'simple', l_(u'Simple Cache')),
        (u'memcached', l_(u'memcached')),
        (u'filesystem', l_(u'Filesystem'))
    ], default=u'null'),
    'memcached_servers':        CommaSeparated(TextField(
                                                    validators=[is_netaddr()]),
                                               default=list),
    'filesystem_cache_path':    TextField(default=u'cache'),

    # email settings
    'smtp_host':                TextField(default=u'localhost'),
    'smtp_port':                IntegerField(default=25),
    'smtp_user':                TextField(default=u''),
    'smtp_password':            TextField(default=u''),
    'smtp_use_tls':             BooleanField(default=False),

    # network settings
    'default_network_timeout':  IntegerField(default=5, help_text=l_(
        u'This timeout is used by default for all network related operations. '
        u'The default should be fine for most environments but if you have a '
        u'very bad network connection during development you should increase '
        u'it.')),

    # plugin settings
    'plugin_guard':             BooleanField(default=not _dev_mode),
    'plugins':                  CommaSeparated(TextField(), default=list),
    'plugin_searchpath':        CommaSeparated(TextField(), default=list,
        help_text=l_(u'It\'s possible to one or more comma '
        u'separated paths here that are searched for plugins.  If the '
        u'is not absolute, it\'s considered relative to the instance '
        u'folder.')),

    # reCAPTCHA settings
    'recaptcha_enable':         BooleanField(default=False, help_text=l_(
        u'If you want to protect forms that non-logged in users or guests can fill out,'
        u' enable it and get your api keys from http://recaptcha.net. Heavily recommended,'
        u' just not enabled per default as you need to get api keys yourself')),
    'recaptcha_use_ssl':        BooleanField(default=True, help_text=l_(
        u'Secure communication between this app and recaptcha over ssl')),
    'recaptcha_public_key':     TextField(default=u''),
    'recaptcha_private_key':    TextField(default=u'')
}

HIDDEN_KEYS = set(('iid', 'secret_key', 'pyclansphere_auth_token',
                   'smtp_password', 'recaptcha_public_key',
                   'recaptcha_private_key'))

def unquote_value(value):
    """Unquote a configuration value."""
    if not value:
        return ''
    if value[0] in '"\'' and value[0] == value[-1]:
        value = value[1:-1].decode('string-escape')
    return value.decode('utf-8')


def quote_value(value):
    """Quote a configuration value."""
    if not value:
        return ''
    if value.strip() == value and value[0] not in '"\'' and \
       value[-1] not in '"\'' and len(value.splitlines()) == 1:
        return value.encode('utf-8')
    return '"%s"' % value.replace('\\', '\\\\') \
                         .replace('\n', '\\n') \
                         .replace('\r', '\\r') \
                         .replace('\t', '\\t') \
                         .replace('"', '\\"').encode('utf-8')


def from_string(value, field):
    """Try to convert a value from string or fall back to the default."""
    try:
        return field(value)
    except ValidationError, e:
        return field.get_default()


# XXX: this function should probably go away, currently it only exists because
# the config editor is not yet updated to use form fields for config vars
def get_converter_name(conv):
    """Get the name of a converter"""
    return {
        bool:   'boolean',
        int:    'integer',
        float:  'float'
    }.get(conv, 'string')


class ConfigurationTransactionError(InternalError):
    """An exception that is raised if the transaction was unable to
    write the changes to the config file.
    """

    help_text = l_(u'''
    <p>
      This error can happen if the configuration file is not writeable.
      Make sure the folder of the configuration file is writeable and
      that the file itself is writeable as well.
    ''')

    def __init__(self, message_or_exception):
        if isinstance(message_or_exception, basestring):
            message = message_or_exception
            error = None
        else:
            message = _(u'Could not save configuration file: %s') % \
                      str(message_or_exception).decode('utf-8', 'ignore')
            error = message_or_exception
        InternalError.__init__(self, message)
        self.original_exception = error


class Configuration(object):
    """Helper class that manages configuration values in a INI configuration
    file.

    >>> app.cfg['clan_title']
    iu'My Title'
    >>> app.cfg.change_single('clan_title', 'Test Title')
    >>> app.cfg['clan_title']
    u'Test Title'
    >>> t = app.cfg.edit(); t.revert_to_default('clan_title'); t.commit()
    """

    def __init__(self, filename):
        self.filename = filename

        self.config_vars = DEFAULT_VARS.copy()
        self._values = {}
        self._converted_values = {}
        self._comments = {}
        self._lock = Lock()

        # if the path does not exist yet set the existing flag to none and
        # set the time timetamp for the filename to something in the past
        if not path.exists(self.filename):
            self.exists = False
            self._load_time = 0
            return

        # otherwise parse the file and copy all values into the internal
        # values dict.  Do that also for values not covered by the current
        # `config_vars` dict to preserve variables of disabled plugins
        self._load_time = path.getmtime(self.filename)
        self.exists = True
        section = 'pyClanSphere'
        current_comment = ''
        f = file(self.filename)
        try:
            for line in f:
                line = line.strip()
                if not line or line[0] in '#;':
                    current_comment += line + '\n'
                    continue
                elif line[0] == '[' and line[-1] == ']':
                    section = line[1:-1].strip()
                    if current_comment.strip():
                        self._comments['[%s]' % section] = current_comment
                    current_comment = ''
                elif '=' not in line:
                    key = line.strip()
                    value = ''
                    if current_comment.strip():
                        self._comments[key] = current_comment
                    current_comment = ''
                else:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    if section != 'pyClanSphere':
                        key = section + '/' + key
                    self._values[key] = unquote_value(value.strip())
                    if current_comment.strip():
                        self._comments[key] = current_comment
                    current_comment = ''
            # comments at the end of the file
            if current_comment.strip():
                self._comments[' end '] = current_comment
        finally:
            f.close()

    def __getitem__(self, key):
        """Return the value for a key."""
        if key.startswith('pyClanSphere/'):
            key = key[5:]
        try:
            return self._converted_values[key]
        except KeyError:
            field = self.config_vars[key]
        try:
            value = from_string(self._values[key], field)
        except KeyError:
            value = field.get_default()
        self._converted_values[key] = value
        return value

    def change_single(self, key, value):
        """Create and commit a transaction for a single key-value-pair."""
        t = self.edit()
        t[key] = value
        t.commit()

    def edit(self):
        """Return a new transaction object."""
        return ConfigTransaction(self)

    def touch(self):
        """Touch the file to trigger a reload."""
        os.utime(self.filename, None)

    @property
    def changed_external(self):
        """True if there are changes on the file system."""
        if not path.isfile(self.filename):
            return False
        return path.getmtime(self.filename) > self._load_time

    def __iter__(self):
        """Iterate over all keys"""
        return iter(self.config_vars)

    iterkeys = __iter__

    def __contains__(self, key):
        """Check if a given key exists."""
        if key.startswith('pyClanSphere/'):
            key = key[5:]
        return key in self.config_vars

    def itervalues(self):
        """Iterate over all values."""
        for key in self:
            yield self[key]

    def iteritems(self):
        """Iterate over all keys and values."""
        for key in self:
            yield key, self[key]

    def values(self):
        """Return a list of values."""
        return list(self.itervalues())

    def keys(self):
        """Return a list of keys."""
        return list(self)

    def items(self):
        """Return a list of all key, value tuples."""
        return list(self.iteritems())

    def export(self):
        """Like iteritems but with the raw values."""
        for key, value in self.iteritems():
            value = self.config_vars[key].to_primitive(value)
            if isinstance(value, basestring):
                yield key, value

    def get_detail_list(self):
        """Return a list of categories with keys and some more
        details for the advanced configuration editor.
        """
        categories = {}

        for key, field in self.config_vars.iteritems():
            if key in self._values:
                use_default = False
                value = field.to_primitive(from_string(self._values[key], field))
            else:
                use_default = True
                value = field.to_primitive(field.get_default())
            if '/' in key:
                category, name = key.split('/', 1)
            else:
                category = 'pyClanSphere'
                name = key
            categories.setdefault(category, []).append({
                'name':         name,
                'field':        field,
                'value':        value,
                'use_default':  use_default
            })

        def sort_func(item):
            """Sort by key, case insensitive, ignore leading underscores and
            move the implicit "pyClanSphere" to the index.
            """
            if item[0] == 'pyClanSphere':
                return 1
            return item[0].lower().lstrip('_')

        return [{
            'items':    sorted(children, key=lambda x: x['name']),
            'name':     key
        } for key, children in sorted(categories.items(), key=sort_func)]

    def get_public_list(self, hide_insecure=False):
        """Return a list of publicly available information about the
        configuration.  This list is safe to share because dangerous keys
        are either hidden or cloaked.
        """
        from pyClanSphere.application import emit_event
        from pyClanSphere.database import secure_database_uri
        result = []
        for key, field in self.config_vars.iteritems():
            value = self[key]
            if hide_insecure:
                if key in HIDDEN_KEYS:
                    value = '****'
                elif key == 'database_uri':
                    value = repr(secure_database_uri(value))
                else:
                    #! this event is emitted if the application wants to
                    #! display a configuration value in a publicly.  The
                    #! return value of the listener is used as new value.
                    #! A listener should return None if the return value
                    #! is not used.
                    for rv in emit_event('cloak-insecure-configuration-var',
                                         key, value):
                        if rv is not None:
                            value = rv
                            break
                    else:
                        value = repr(value)
            else:
                value = repr(value)
            result.append({
                'key':          key,
                'default':      repr(field.get_default()),
                'value':        value
            })
        result.sort(key=lambda x: x['key'].lower())
        return result

    def __len__(self):
        return len(self.config_vars)

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, dict(self.items()))


class ConfigTransaction(object):
    """A configuration transaction class. Instances of this class are returned
    by Config.edit(). Changes can then be added to the transaction and
    eventually be committed and saved to the file system using the commit()
    method.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self._values = {}
        self._converted_values = {}
        self._remove = []
        self._committed = False

    def __getitem__(self, key):
        """Get an item from the transaction or the underlaying config."""
        if key in self._converted_values:
            return self._converted_values[key]
        elif key in self._remove:
            return self.cfg.config_vars[key][1]
        return self.cfg[key]

    def __setitem__(self, key, value):
        """Set the value for a key by a python value."""
        self._assert_uncommitted()

        # do not change if we already have the same value.  Otherwise this
        # would override defaulted values.
        if value == self[key]:
            return

        if key.startswith('pyClanSphere/'):
            key = key[5:]
        if key not in self.cfg.config_vars:
            raise KeyError(key)
        if isinstance(value, str):
            value = value.decode('utf-8')
        field = self.cfg.config_vars[key]
        self._values[key] = field.to_primitive(value)
        self._converted_values[key] = value

    def _assert_uncommitted(self):
        if self._committed:
            raise ValueError('This transaction was already committed.')

    def set_from_string(self, key, value, override=False):
        """Set the value for a key from a string."""
        self._assert_uncommitted()
        if key.startswith('pyClanSphere/'):
            key = key[5:]
        field = self.cfg.config_vars[key]
        new = from_string(value, field)
        old = self._converted_values.get(key, None) or self.cfg[key]
        if override or field.to_primitive(old) != field.to_primitive(new):
            self[key] = new

    def revert_to_default(self, key):
        """Revert a key to the default value."""
        self._assert_uncommitted()
        if key.startswith('pyClanSphere'):
            key = key[5:]
        self._remove.append(key)

    def update(self, *args, **kwargs):
        """Update multiple items at once."""
        for key, value in dict(*args, **kwargs).iteritems():
            self[key] = value

    def commit(self):
        """Commit the transactions. This first tries to save the changes to the
        configuration file and only updates the config in memory when that is
        successful.
        """
        self._assert_uncommitted()
        if not self._values and not self._remove:
            self._committed = True
            return
        self.cfg._lock.acquire()
        try:
            all = self.cfg._values.copy()
            all.update(self._values)
            for key in self._remove:
                all.pop(key, None)

            sections = {}
            for key, value in all.iteritems():
                if '/' in key:
                    section, key = key.split('/', 1)
                else:
                    section = 'pyClanSphere'
                sections.setdefault(section, []).append((key, value))
            pyClanSphere_section = sections.pop('pyClanSphere')
            sections = [('pyClanSphere', pyClanSphere_section)] + sorted(sections.items())
            for section in sections:
                section[1].sort()

            try:
                f = file(self.cfg.filename, 'w')
                try:
                    for idx, (section, items) in enumerate(sections):
                        if '[%s]' % section in self.cfg._comments:
                            f.write(self.cfg._comments['[%s]' % section])
                        elif idx:
                            f.write('\n')
                        f.write('[%s]\n' % section.encode('utf-8'))
                        for key, value in items:
                            if section != 'pyClanSphere':
                                ckey = '%s/%s' % (section, key)
                            else:
                                ckey = key
                            if ckey in self.cfg._comments:
                                f.write(self.cfg._comments[ckey])
                            f.write('%s = %s\n' % (key, quote_value(value)))
                    if ' end ' in self.cfg._comments:
                        f.write(self.cfg._comments[' end '])
                finally:
                    f.close()
            except IOError, e:
                log.error('Could not write configuration: %s' % e, 'config')
                raise ConfigurationTransactionError(e)
            self.cfg._values.update(self._values)
            self.cfg._converted_values.update(self._converted_values)
            for key in self._remove:
                self.cfg._values.pop(key, None)
                self.cfg._converted_values.pop(key, None)
        finally:
            self.cfg._lock.release()
        self._committed = True
