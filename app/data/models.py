from app import log, db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import UniqueConstraint
import datetime, json
from babel.dates import get_day_names, get_month_names


# woensdag 24 februari om 14 uur
def datetime_to_dutch_datetime_string(date):
    try:
        date_string = f'{get_day_names(locale="nl")[date.weekday()]} {date.day} {get_month_names(locale="nl")[date.month]} om {date.strftime("%H.%M")}'
        return date_string
    except:
        return ''


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    class USER_TYPE:
        LOCAL = 'local'
        OAUTH = 'oauth'

    @staticmethod
    def get_zipped_types():
        return list(zip(['local', 'oauth'], ['LOCAL', 'OAUTH']))

    class LEVEL:
        USER = 1
        SUPERVISOR = 3
        ADMIN = 5

        ls = ["GEBRUIKER", "SECRETARIAAT", "ADMINISTRATOR"]

        @staticmethod
        def i2s(i):
            if i == 1:
                return User.LEVEL.ls[0]
            elif i == 3:
                return User.LEVEL.ls[1]
            if i == 5:
                return User.LEVEL.ls[2]

    @staticmethod
    def get_zipped_levels():
        return list(zip(["1", "3", "5"], User.LEVEL.ls))

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256))
    username = db.Column(db.String(256))
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    password_hash = db.Column(db.String(256))
    level = db.Column(db.Integer)
    user_type = db.Column(db.String(256))
    last_login = db.Column(db.DateTime())
    settings = db.relationship('Settings', cascade='all, delete', backref='user', lazy='dynamic')

    @property
    def is_local(self):
        return self.user_type == User.USER_TYPE.LOCAL

    @property
    def is_oauth(self):
        return self.user_type == User.USER_TYPE.OAUTH

    @property
    def is_at_least_user(self):
        return self.level >= User.LEVEL.USER

    @property
    def is_strict_user(self):
        return self.level == User.LEVEL.USER

    @property
    def is_at_least_supervisor(self):
        return self.level >= User.LEVEL.SUPERVISOR

    @property
    def is_at_least_admin(self):
        return self.level >= User.LEVEL.ADMIN

    @property
    def password(self):
        raise AttributeError('Paswoord kan je niet lezen.')

    @password.setter
    def password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        else:
            return True

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def log(self):
        return '<User: {}/{}>'.format(self.id, self.username)

    def ret_dict(self):
        return {'id': self.id, 'DT_RowId': self.id, 'email': self.email, 'username': self.username,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'level': User.LEVEL.i2s(self.level), 'user_type': self.user_type, 'last_login': self.last_login,
                'chbx': ''}


class Settings(db.Model):
    __tablename__ = 'settings'

    class SETTING_TYPE:
        E_INT = 'INT'
        E_STRING = 'STRING'
        E_FLOAT = 'FLOAT'
        E_BOOL = 'BOOL'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    value = db.Column(db.Text)
    type = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    UniqueConstraint('name', 'user_id')

    def log(self):
        return '<Setting: {}/{}/{}/{}>'.format(self.id, self.name, self.value, self.type)


class Guest(db.Model):
    __tablename__ = 'guests'

    class SUBSCRIBE:
        EMAIL_INVITE_SENT = 'email-invite-sent'
        NBR_INVITE_SENT =   'nbr-invite-sent'
        EMAIL_ACK_SENT =    'email-ack-sent'
        NBR_ACK_SENT =      'nbr-ack-sent'
        EMAIL_CANCEL_SENT = 'email-cancel-sent'
        NBR_CANCEL_SENT =   'nbr-cancel-sent'
        NBR_EMAIL_RETRY =   'nbr-email-retry'
        ENABLED =           'enabled'
        ALL =               'all'

        cb = {}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256))
    phone = db.Column(db.String(256))
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    full_name = db.Column(db.String(256))
    child_name = db.Column(db.String(256))
    key = db.Column(db.String(256))
    note = db.Column(db.Text)
    last_login = db.Column(db.DateTime())
    invite_email_sent = db.Column(db.Boolean, default=True)
    nbr_invite_sent = db.Column(db.Integer(), default=0)
    ack_email_sent = db.Column(db.Boolean, default=True)
    nbr_ack_sent = db.Column(db.Integer(), default=0)
    cancel_email_sent = db.Column(db.Boolean, default=True)
    nbr_cancel_sent = db.Column(db.Integer(), default=0)
    email_send_retry = db.Column(db.Integer(), default=0)
    enabled = db.Column(db.Boolean, default=True)
    code = db.Column(db.String(256), default='')
    timeslot = db.Column(db.DateTime())
    misc_field = db.Column(db.Text)

    def row_color(self):
        if self.enabled:
            if 0 == (self.nbr_invite_sent + self.nbr_ack_sent):
                return 'yellow'
            else:
                return ''
        else:
            return 'lightsalmon'

    def flat(self):
        flat = {
            'id': self.id,
            'phone': self.phone,
            'email': self.email,
            'first-name': self.first_name,
            'last-name': self.last_name,
            'full_name': self.full_name,
            'child_name': self.child_name,
            'key': self.key,
            'note': self.note,
            'last_login': self.last_login,
            'reservation-code': self.code,
            'invite_email_sent': self.invite_email_sent,
            'nbr_invite_sent': self.nbr_invite_sent,
            'ack_email_sent': self.ack_email_sent,
            'nbr_ack_sent': self.nbr_ack_sent,
            'cancel_email_sent': self.cancel_email_sent,
            'nbr_cancel_sent': self.nbr_cancel_sent,
            'email_send_retry': self.email_send_retry,
            'enabled': self.enabled,
            'timeslot': datetime_to_dutch_datetime_string(self.timeslot),
            'overwrite_row_color': self.row_color(),
        }
        misc_field = json.loads(self.misc_field) if self.misc_field else ''
        flat.update(misc_field)
        return flat


    def set(self, type, value):
        if type == self.SUBSCRIBE.EMAIL_INVITE_SENT:
            self.invite_email_sent = value
        elif type == self.SUBSCRIBE.NBR_INVITE_SENT:
            self.nbr_invite_sent = value
        elif type == self.SUBSCRIBE.EMAIL_ACK_SENT:
            self.ack_email_sent = value
        elif type == self.SUBSCRIBE.NBR_ACK_SENT:
            self.nbr_ack_sent = value
        elif type == self.SUBSCRIBE.EMAIL_CANCEL_SENT:
            self.cancel_email_sent = value
        elif type == self.SUBSCRIBE.NBR_CANCEL_SENT:
            self.nbr_cancel_sent = value
        elif type == self.SUBSCRIBE.NBR_EMAIL_RETRY:
            self.email_send_retry = value
        elif type == self.SUBSCRIBE.ENABLED:
            self.enabled = value
        else:
            return False
        db.session.commit()
        if type in self.SUBSCRIBE.cb:
            for cb in self.SUBSCRIBE.cb[type]:
                cb[0](type, value, cb[1])
        if self.SUBSCRIBE.ALL in self.SUBSCRIBE.cb:
            for cb in self.SUBSCRIBE.cb[self.SUBSCRIBE.ALL]:
                cb[0](self.SUBSCRIBE.ALL, value, cb[1])
        return True


    @staticmethod
    def subscribe(type, cb, opaque):
        if type not in Guest.SUBSCRIBE.cb:
            Guest.SUBSCRIBE.cb[type] = []
        Guest.SUBSCRIBE.cb[type].append((cb, opaque))
        return True


class TimeslotConfiguration(db.Model):
    __tablename__ = 'timeslot_configurations'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime())
    length = db.Column(db.Integer, default=15)  # in minutes
    nbr_of_timeslots = db.Column(db.Integer, default=20)
    items_per_timeslot = db.Column(db.Integer, default=8)
    active = db.Column(db.Boolean, default=True)

    def flat(self):
        return {
            'id': self.id,
            'active': self.active,
            'date': datetime_to_dutch_datetime_string(self.date),
            'overwrite_row_color': self.row_color(),
        }

