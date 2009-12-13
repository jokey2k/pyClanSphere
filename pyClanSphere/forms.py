# -*- coding: utf-8 -*-
"""
    pyClanSphere.forms
    ~~~~~~~~~~~~~~~~~~

    The form classes the pyClanSphere core uses.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from copy import copy

from pyClanSphere.i18n import _, lazy_gettext, list_languages
from pyClanSphere.application import get_application, get_request, emit_event
from pyClanSphere.config import DEFAULT_VARS
from pyClanSphere.database import db, notification_subscriptions
from pyClanSphere.models import User, Group, NotificationSubscription, IMAccount
from pyClanSphere.privileges import bind_privileges
from pyClanSphere.notifications import send_notification_template
from pyClanSphere.utils import forms, log, dump_json
from pyClanSphere.utils.http import redirect_to
from pyClanSphere.utils.validators import ValidationError, is_valid_email, \
     is_valid_url, is_valid_slug, is_netaddr, is_not_whitespace_only
from pyClanSphere.utils.redirects import register_redirect


def config_field(cfgvar, label=None, **kwargs):
    """Helper function for fetching fields from the config."""
    if isinstance(cfgvar, forms.Field):
        field = copy(cfgvar)
    else:
        field = copy(DEFAULT_VARS[cfgvar])
    field._position_hint = forms._next_position_hint()
    if label is not None:
        field.label = label
    for name, value in kwargs.iteritems():
        setattr(field, name, value)
    return field


class LoginForm(forms.Form):
    """The form for the login page."""
    user = forms.ModelField(User, 'username', required=True, messages=dict(
        not_found=lazy_gettext(u'User “%(value)s” does not exist.'),
        required=lazy_gettext(u'You have to enter a username.')
    ), on_not_found=lambda user:
        log.warning(_(u'Failed login attempt, user “%s” does not exist')
                      % user, 'auth')
    )
    password = forms.TextField(widget=forms.PasswordInput)
    permanent = forms.BooleanField()

    def context_validate(self, data):
        if not data['user'].check_password(data['password']):
            log.warning(_(u'Failed login attempt from “%s”, invalid password')
                        % data['user'].username, 'auth')
            raise ValidationError(_('Incorrect password.'))


class ChangePasswordForm(forms.Form):
    """The form used on the password-change dialog in the admin panel."""
    old_password = forms.TextField(lazy_gettext(u'Old password'), required=True,
                                   widget=forms.PasswordInput)
    new_password = forms.TextField(lazy_gettext(u'New password'), required=True,
                                   widget=forms.PasswordInput)
    check_password = forms.TextField(lazy_gettext(u'Repeat password'),
                                     required=True,
                                     widget=forms.PasswordInput)

    def __init__(self, user, initial=None):
        forms.Form.__init__(self, initial)
        self.user = user

    def validate_old_password(self, value):
        if not self.user.check_password(value):
            raise ValidationError(_('The old password you\'ve '
                                    'entered is wrong.'))

    def context_validate(self, data):
        if data['new_password'] != data['check_password']:
            raise ValidationError(_('The two passwords don\'t match.'))


class PluginForm(forms.Form):
    """The form for plugin activation and deactivation."""
    active_plugins = forms.MultiChoiceField(widget=forms.CheckboxGroup)
    disable_guard = forms.BooleanField(lazy_gettext(u'Disable plugin guard'),
        help_text=lazy_gettext(u'If the plugin guard is disabled errors '
                               u'on plugin setup are not caught.'))

    def __init__(self, initial=None):
        self.app = app = get_application()
        self.active_plugins.choices = sorted([(x.name, x.display_name)
                                              for x in app.plugins.values()],
                                             key=lambda x: x[1].lower())
        if initial is None:
            initial = dict(
                active_plugins=[x.name for x in app.plugins.itervalues()
                                if x.active]
            )
        forms.Form.__init__(self, initial)

    def apply(self):
        """Apply the changes."""
        t = self.app.cfg.edit()
        t['plugins'] = u', '.join(sorted(self.data['active_plugins']))
        t.commit()


class RemovePluginForm(forms.Form):
    """Dummy form for plugin removing."""

    def __init__(self, plugin):
        forms.Form.__init__(self)
        self.plugin = plugin




class _GroupBoundForm(forms.Form):
    """Internal baseclass for group bound forms."""

    def __init__(self, group, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.group = group

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.group = self.group
        widget.new = self.group is None
        return widget


class EditGroupForm(_GroupBoundForm):
    """Edit or create a group."""

    groupname = forms.TextField(lazy_gettext(u'Groupname'), max_length=30,
                                validators=[is_not_whitespace_only()],
                                required=True)
    privileges = forms.MultiChoiceField(lazy_gettext(u'Privileges'),
                                        widget=forms.CheckboxGroup)

    def __init__(self, group=None, initial=None):
        if group is not None:
            initial = forms.fill_dict(initial,
                groupname=group.name,
                privileges=[x.name for x in group.privileges]
            )
        _GroupBoundForm.__init__(self, group, initial)
        self.privileges.choices = self.app.list_privileges()

    def validate_groupname(self, value):
        query = Group.query.filter_by(name=value)
        if self.group is not None:
            query = query.filter(Group.id != self.group.id)
        if query.first() is not None:
            raise ValidationError(_('This groupname is already in use'))

    def _set_common_attributes(self, group):
        forms.set_fields(group, self.data)
        bind_privileges(group.privileges, self.data['privileges'])

    def make_group(self):
        """A helper function that creates a new group object."""
        group = Group(self.data['groupname'])
        self._set_common_attributes(group)
        self.group = group
        return group

    def save_changes(self):
        """Apply the changes."""
        self.group.name = self.data['groupname']
        self._set_common_attributes(self.group)


class DeleteGroupForm(_GroupBoundForm):
    """Used to delete a group from the admin panel."""

    action = forms.ChoiceField(lazy_gettext(u'What should pyClanSphere do with users '
                                            u'assigned to this group?'),
                              choices=[
        ('delete_membership', lazy_gettext(u'Do nothing, just detach the membership')),
        ('relocate', lazy_gettext(u'Move the users to another group'))
    ], widget=forms.RadioButtonGroup)
    relocate_to = forms.ModelField(Group, 'id', lazy_gettext(u'Relocate users to'),
                                   widget=forms.SelectBox)

    def __init__(self, group, initial=None):
        self.relocate_to.choices = [('', u'')] + [
            (g.id, g.name) for g in Group.query.filter(Group.id != group.id)
        ]

        _GroupBoundForm.__init__(self, group, forms.fill_dict(initial,
            action='delete_membership'))

    def context_validate(self, data):
        if data['action'] == 'relocate' and not data['relocate_to']:
            raise ValidationError(_('You have to select a group that '
                                    'gets the users assigned.'))

    def delete_group(self):
        """Deletes a group."""
        if self.data['action'] == 'relocate':
            new_group = Group.query.filter_by(self.data['reassign_to'].id).first()
            for user in self.group.users:
                if not new_group in user.groups:
                    user.groups.append(new_group)
        db.commit()

        #! plugins can use this to react to user deletes.  They can't stop
        #! the deleting of the group but they can delete information in
        #! their own tables so that the database is consistent afterwards.
        #! Additional to the group object the form data is submitted.
        emit_event('before-group-deleted', self.group, self.data)
        db.delete(self.group)


class _UserBoundForm(forms.Form):
    """Internal baseclass for user bound forms."""

    username = forms.TextField(lazy_gettext(u'Username'), max_length=30,
                               validators=[is_not_whitespace_only()],
                               required=True)
    real_name = forms.TextField(lazy_gettext(u'Realname'), max_length=180)
    display_name = forms.ChoiceField(lazy_gettext(u'Display name'))
    email = forms.TextField(lazy_gettext(u'Email'), required=True,
                            validators=[is_valid_email()])
    www = forms.TextField(lazy_gettext(u'Website'),
                          validators=[is_valid_url()])
    gender_male = forms.ChoiceField(lazy_gettext(u'Gender'))
    birthday = forms.DateField(lazy_gettext(u'Day of Birth'))
    height = forms.IntegerField(lazy_gettext(u'Height in full cm'))
    address = forms.TextField(lazy_gettext('Streetaddress'))
    zip = forms.IntegerField(lazy_gettext(u'Zip code'))
    city = forms.TextField(lazy_gettext(u'City'))
    country = forms.TextField(lazy_gettext(u'Country'))

    def __init__(self, user, initial=None):
        if user is not None:
            initial = forms.fill_dict(initial,
                username=user.username,
                real_name=user.real_name,
                display_name=user._display_name,
                gender_male=user.gender_male,
                birthday=user.birthday,
                height=user.height,
                address=user.address,
                zip=user.zip,
                city=user.city,
                country=user.country,
                email=user.email,
                www=user.www
            )
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.user = user
        self.display_name.choices = [
            (u'$username', user and user.username or _('Username')),
            (u'$real_name', user and user.real_name or _('Realname'))
        ]
        self.gender_male.choices = [
            (1, _('Male')),
            (0, _('Female'))
        ]

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.user = self.user
        widget.new = self.user is None
        return widget

    def _set_common_attributes(self, user):
        forms.set_fields(user, self.data, 'www', 'real_name', 'birthday',
                         'display_name', 'height', 'address', 'zip', 'city',
                         'country')

    def save_changes(self):
        """Apply the changes."""
        self.user.username = self.data['username']
        if self.data['password']:
            self.user.set_password(self.data['password'])
        self.user.email = self.data['email']
        self._set_common_attributes(self.user)


class EditUserForm(_UserBoundForm):
    """Edit or create a user."""

    privileges = forms.MultiChoiceField(lazy_gettext(u'Privileges'),
                                        widget=forms.CheckboxGroup)
    groups = forms.MultiChoiceField(lazy_gettext(u'Groups'),
                                    widget=forms.CheckboxGroup)
    password = forms.TextField(lazy_gettext(u'Password'),
                               widget=forms.PasswordInput)
    password_confirm = forms.TextField(lazy_gettext(u'Confirm password'),
                                       widget=forms.PasswordInput)

    def __init__(self, user=None, initial=None):
        if user is not None:
            initial = forms.fill_dict(initial,
                privileges=[x.name for x in user.own_privileges],
                groups=[g.name for g in user.groups]
            )
        _UserBoundForm.__init__(self, user, initial)
        self.privileges.choices = self.app.list_privileges()
        self.groups.choices = [g.name for g in Group.query.all()]
        self.password.required = user is None

    def context_validate(self, data):
        if data['password'] != data['password_confirm']:
            raise ValidationError(_('The two passwords don\'t match.'))

    def validate_username(self, value):
        query = User.query.filter_by(username=value)
        if self.user is not None:
            query = query.filter(User.id != self.user.id)
        if query.first() is not None:
            raise ValidationError(_('This username is already in use'))

    def _set_common_attributes(self, user):
        _UserBoundForm._set_common_attributes(self, user)
        bind_privileges(user.own_privileges, self.data['privileges'], user)
        bound_groups = set(g.name for g in user.groups)
        choosen_groups = set(self.data['groups'])
        group_mapping = dict((g.name, g) for g in Group.query.all())
        # delete groups
        for group in (bound_groups - choosen_groups):
            user.groups.remove(group_mapping[group])
        # and add new groups
        for group in (choosen_groups - bound_groups):
            user.groups.append(group_mapping[group])

    def make_user(self):
        """A helper function that creates a new user object."""
        user = User(self.data['username'], self.data['password'],
                    self.data['email'])
        self._set_common_attributes(user)
        self.user = user
        return user

class DeleteUserForm(_UserBoundForm):
    """Used to delete a user from the admin panel."""

    def delete_user(self):
        """Deletes the user."""
        #! plugins can use this to react to user deletes.  They can't stop
        #! the deleting of the user but they can delete information in
        #! their own tables so that the database is consistent afterwards.
        #! Additional to the user object the form data is submitted.
        emit_event('before-user-deleted', self.user, self.data)
        db.delete(self.user)

class _IMAccountBoundForm(forms.Form):
    """Internal baseclass for im account bound forms."""

    def __init__(self, imaccount, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.imaccount = imaccount

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.imaccount = self.imaccount
        widget.new = self.imaccount is None
        return widget

class EditIMAccountForm(_IMAccountBoundForm):
    """Update Players' IM Accounts."""

    service = forms.TextField(lazy_gettext(u'Service'),
                              widget=forms.SelectBox)
    username = forms.ModelField(User, 'id', lazy_gettext(u'User'),
                            widget=forms.SelectBox)
    account = forms.TextField(lazy_gettext(u'Account ID'), max_length=100,
                              validators=[is_not_whitespace_only()])

    def __init__(self, user=None, imaccount=None, initial=None):
        if imaccount is not None:
            initial = forms.fill_dict(initial,
                service=imaccount.service,
                account=imaccount.account,
                username=user.id if user is not None else None
            )
        _IMAccountBoundForm.__init__(self, imaccount, initial)
        self.user = user
        self.service.choices = [(k, v) for k, v in IMAccount.known_services.iteritems()]
        self.username.choices = [(user.id, user.display_name) for user in User.query.all()]

    def make_imaccount(self):
        """A helper function that creates new IMAccount objects."""
        imaccount = IMAccount(self.user if self.user is not None \
                              else User.query.get(self.data['username']),
                              self.data['service'], self.data['account'])

        self.imaccount = imaccount
        return imaccount

    def context_validate(self, data):
        query = IMAccount.query.filter_by(service=data['service']).filter_by(account=data['account'])
        if self.imaccount is not None:
            query = query.filter(IMAccount.id != self.imaccount.id)
        if query.first() is not None:
            raise ValidationError(_('This account is already registered'))

    def _set_common_attributes(self, imaccount):
        imaccount.user = self.user if self.user else User.query.get(self.data['username'])
        forms.set_fields(imaccount, self.data, 'service', 'account')

    def save_changes(self):
        """Apply the changes."""

        self._set_common_attributes(self.imaccount)

class DeleteIMAccountForm(_IMAccountBoundForm):
    """Used to remove a member from a squad."""

    def delete_account(self):
        """Deletes the im account."""
        db.delete(self.imaccount)

class EditProfileForm(_UserBoundForm):
    """Edit or create a user's profile."""

    def __init__(self, user=None, initial=None):
        _UserBoundForm.__init__(self, user, initial)

    def validate_email(self, value):
        query = User.query.filter_by(email=value)
        if self.user is not None:
            query = query.filter(User.id != self.user.id)
        if query.first() is not None:
            raise ValidationError(_('This email address is already in use'))

    def validate_password(self, value):
        if 'password_confirm' in self.data:
            password_confirm = self.data['password_confirm']
        else:
            password_confirm = self.request.values.get('password_confirm', '')
        if ((not value == password_confirm) or (value and not password_confirm)
            or (password_confirm and not value)):
            raise ValidationError(_('Passwords do not match'))


class DeleteAccountForm(_UserBoundForm):
    """Used for a user to delete a his own account."""

    def __init__(self, user, initial=None):
        _UserBoundForm.__init__(self, user, forms.fill_dict(initial,
            action='delete'
        ))

    def delete_user(self):
        """Deletes the user's account."""
        # find all the comments by this author and make them comments that
        # are no longer linked to the author.
        for comment in self.user.comments.all():
            comment.unbind_user()

        #! plugins can use this to react to user deletes.  They can't stop
        #! the deleting of the user but they can delete information in
        #! their own tables so that the database is consistent afterwards.
        #! Additional to the user object the form data is submitted.
        emit_event('before-user-deleted', self.user, self.data)
        db.delete(self.user)


class _ConfigForm(forms.Form):
    """Internal baseclass for forms that operate on config values."""

    def __init__(self, initial=None):
        self.app = get_application()
        if initial is None:
            initial = {}
            for name in self.fields:
                initial[name] = self.app.cfg[name]
        forms.Form.__init__(self, initial)

    def _apply(self, t, skip):
        for key, value in self.data.iteritems():
            if key not in skip:
                t[key] = value

    def apply(self):
        t = self.app.cfg.edit()
        self._apply(t, set())
        t.commit()


class LogOptionsForm(_ConfigForm):
    """A form for the logfiles."""
    log_file = config_field('log_file', lazy_gettext(u'Filename'))
    log_level = config_field('log_level', lazy_gettext(u'Log Level'))


class BasicOptionsForm(_ConfigForm):
    """The form where the basic options are changed."""
    clan_title = config_field('clan_title', lazy_gettext(u'Clan Page title'))
    clan_tagline = config_field('clan_tagline', lazy_gettext(u'Clan Page tagline'))
    clan_email = config_field('clan_email', lazy_gettext(u'Clan email'))
    language = config_field('language', lazy_gettext(u'Language'))
    timezone = config_field('timezone', lazy_gettext(u'Timezone'))
    session_cookie_name = config_field('session_cookie_name',
                                       lazy_gettext(u'Cookie Name'))

    def __init__(self, initial=None):
        _ConfigForm.__init__(self, initial)
        self.language.choices = list_languages()


class URLOptionsForm(_ConfigForm):
    """The form for url changes.  This form sends database queries, even
    though seems to only operate on the config.  Make sure to commit.
    """

    admin_url_prefix = config_field('admin_url_prefix',
                                    lazy_gettext(u'Admin URL prefix'))
    account_url_prefix = config_field('account_url_prefix',
                                    lazy_gettext(u'Account URL prefix'))
    force_https = config_field('force_https', lazy_gettext(u'Force HTTPS'))

    def _apply(self, t, skip):
        for key, value in self.data.iteritems():
            if key not in skip:
                old = t[key]
                if old != value:
                    t[key] = value

        # update the site_url based on the force_https flag.
        site_url = (t['force_https'] and 'https' or 'http') + \
                   ':' + t['site_url'].split(':', 1)[1]
        if site_url != t['site_url']:
            t['site_url'] = site_url


class ThemeOptionsForm(_ConfigForm):
    """
    The form for theme changes.  This is mainly just a dummy,
    to get csrf protection working.
    """


class CacheOptionsForm(_ConfigForm):
    cache_system = config_field('cache_system', lazy_gettext(u'Cache system'))
    cache_timeout = config_field('cache_timeout',
                                 lazy_gettext(u'Default cache timeout'))
    enable_eager_caching = config_field('enable_eager_caching',
                                        lazy_gettext(u'Enable eager caching'),
                                        help_text=lazy_gettext(u'Enable'))
    memcached_servers = config_field('memcached_servers')
    filesystem_cache_path = config_field('filesystem_cache_path')

    def context_validate(self, data):
        if data['cache_system'] == 'memcached':
            if not data['memcached_servers']:
                raise ValidationError(_(u'You have to provide at least one '
                                        u'server to use memcached.'))
        elif data['cache_system'] == 'filesystem':
            if not data['filesystem_cache_path']:
                raise ValidationError(_(u'You have to provide cache folder to '
                                        u'use filesystem cache.'))


class MaintenanceModeForm(forms.Form):
    """yet a dummy form, but could be extended later."""


class DeleteImportForm(forms.Form):
    """This form is used to delete a imported file."""


class ExportForm(forms.Form):
    """This form is used to implement the export dialog."""


def make_config_form():
    """Returns the form for the configuration editor."""
    app = get_application()
    fields = {}
    values = {}
    use_default_label = lazy_gettext(u'Use default value')

    for category in app.cfg.get_detail_list():
        items = {}
        values[category['name']] = category_values = {}
        for item in category['items']:
            items[item['name']] = forms.Mapping(
                value=item['field'],
                use_default=forms.BooleanField(use_default_label)
            )
            category_values[item['name']] = {
                'value':        item['value'],
                'use_default':  False
            }
        fields[category['name']] = forms.Mapping(**items)

    class _ConfigForm(forms.Form):
        values = forms.Mapping(**fields)
        cfg = app.cfg

        def apply(self):
            t = self.cfg.edit()
            for category, items in self.data['values'].iteritems():
                for key, d in items.iteritems():
                    if category != 'pyClanSphere':
                        key = '%s/%s' % (category, key)
                    if d['use_default']:
                        t.revert_to_default(key)
                    else:
                        t[key] = d['value']
            t.commit()

    return _ConfigForm({'values': values})


def make_notification_form(user):
    """Creates a notification form."""
    app = get_application()
    fields = {}
    subscriptions = {}

    systems = [(s.key, s.name) for s in
               sorted(app.notification_manager.systems.values(),
                      key=lambda x: x.name.lower())]

    for obj in app.notification_manager.types(user):
        fields[obj.name] = forms.MultiChoiceField(choices=systems,
                                                  label=obj.description,
                                                  widget=forms.CheckboxGroup)

    for ns in user.notification_subscriptions:
        subscriptions.setdefault(ns.notification_id, []) \
            .append(ns.notification_system)

    class _NotificationForm(forms.Form):
        subscriptions = forms.Mapping(**fields)
        system_choices = systems

        def apply(self):
            user_subscriptions = {}
            for subscription in user.notification_subscriptions:
                user_subscriptions.setdefault(subscription.notification_id,
                    set()).add(subscription.notification_system)

            for key, active in self['subscriptions'].iteritems():
                currently_set = user_subscriptions.get(key, set())
                active = set(active)

                # remove outdated
                for system in currently_set.difference(active):
                    for subscription in user.notification_subscriptions \
                        .filter_by(notification_id=key,
                                   notification_system=system):
                        db.session.delete(subscription)

                # add new
                for system in active.difference(currently_set):
                    user.notification_subscriptions.append(
                        NotificationSubscription(user=user, notification_id=key,
                                                 notification_system=system))

    return _NotificationForm({'subscriptions': subscriptions})

