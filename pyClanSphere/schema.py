# -*- coding: utf-8 -*-
"""
    pyClanSphere.schema
    ~~~~~~~~~~~~~~~~~~~

    Database schema for our core models
    
    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime

from pyClanSphere.database import db, metadata

users = db.Table('users', metadata,
    db.Column('user_id', db.Integer, primary_key=True),
    db.Column('username', db.String(30)),
    db.Column('real_name', db.String(180)),
    db.Column('display_name', db.String(180)),
    db.Column('gender_male', db.Boolean),
    db.Column('birthday', db.DateTime),
    db.Column('height', db.Integer),
    db.Column('address', db.String(250)),
    db.Column('zip', db.Integer),
    db.Column('city', db.String(250)),
    db.Column('country', db.String(200)),
    db.Column('pw_hash', db.String(70)),
    db.Column('email', db.String(250)),
    db.Column('www', db.String(200)),
    db.Column('creation_date', db.DateTime, nullable=False,
              default=datetime.utcnow()),
    db.Column('last_visited', db.DateTime),
    db.Column('notes', db.Text)
)

groups = db.Table('groups', metadata,
    db.Column('group_id', db.Integer, primary_key=True),
    db.Column('name', db.String(30))
)

group_users = db.Table('group_users', metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.group_id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'))
)

privileges = db.Table('privileges', metadata,
    db.Column('privilege_id', db.Integer, primary_key=True),
    db.Column('name', db.String(50), unique=True)
)

user_privileges = db.Table('user_privileges', metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id')),
    db.Column('privilege_id', db.Integer,
              db.ForeignKey('privileges.privilege_id'))
)

group_privileges = db.Table('group_privileges', metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.group_id')),
    db.Column('privilege_id', db.Integer,
              db.ForeignKey('privileges.privilege_id'))
)

redirects = db.Table('redirects', metadata,
    db.Column('redirect_id', db.Integer, primary_key=True),
    db.Column('original', db.String(200), unique=True),
    db.Column('new', db.String(200))
)

notification_subscriptions = db.Table('notification_subscriptions', metadata,
    db.Column('subscription_id', db.Integer, primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id')),
    db.Column('notification_system', db.String(50)),
    db.Column('notification_id', db.String(100)),
    db.UniqueConstraint('user_id', 'notification_system', 'notification_id')
)

imaccounts = db.Table('imaccounts', metadata,
    db.Column('account_id', db.Integer, primary_key=True),
    db.Column('user_id', db.ForeignKey('users.user_id')),
    db.Column('service', db.Integer),
    db.Column('account', db.String(64)),
    db.UniqueConstraint('user_id', 'service', 'account')
)

passwordrequests = db.Table('passwordrequests', metadata,
    db.Column('req_id', db.String(36), primary_key=True),
    db.Column('user_id', db.ForeignKey('users.user_id')),
    db.Column('ip', db.String(64)),
    db.Column('requesttime', db.DateTime)
)
