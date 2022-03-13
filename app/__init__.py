from flask import Flask, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_jsglue import JSGlue
from werkzeug.routing import IntegerConverter as OrigIntegerConvertor
import logging.handlers, os, sys
from functools import wraps
from flask_socketio import SocketIO
from flask_apscheduler import APScheduler
from flask_mail import Mail


flask_app = Flask(__name__, instance_relative_config=True, template_folder='presentation/templates/')

# Configuration files...
from config import app_config
config_name = os.getenv('FLASK_CONFIG')
config_name = config_name if config_name else 'production'
flask_app.config.from_object(app_config[config_name])
flask_app.config.from_pyfile('config.py')

# V0.1: copy from redeem-voucher V0.21
# V0.2: made generic adaptations
# V0.3: update systemfiles
# V0.4: make more generic
# V0.5: send all invite emails button did not work
# V0.6: reworked the reservations-list
# V0.7: small bugfix
# V0.8: added miscellaneous fields
# V0.9: small bugfix, default JSON value should be {}
# V0.10: enable search in misc_field
# V0.11: bugfix to make new reservations possible
# V0.12: small bugfix
# V0.13: remove yellow row color when invite or ack mail is sent
# V0.14: small bugfix with counters.  Added invitation reminder mail prefix
# V0.15: escape url specific characters in data
# V0.16: bugfix: when adding a new but empty reservation, show error
# V0.17: update in logging: add correct app name
# V0.18: update in title of registration form
# V0.19: update in favicon of registration form
# V0.20: registration-ok html form can be set via admin settings
# V0.21: added message no-timeslot
# V0.22: bugifx timeslot-list
# V0.23: log when registration is cancelled
# V0.24: refactored callbacks in some Guest settings
# V0.25: implemented cancel-registration-mail
# V0.26: send cancel-registration-mail when guest pushes cancel registration button
# V0.27: add setting: enable timeslot registration

@flask_app.context_processor
def inject_defaults():
    return dict(version='V0.27', title=flask_app.config['HTML_TITLE'], site_name=flask_app.config['SITE_NAME'])


#  enable logging
log = logging.getLogger(flask_app.config['LOG_HANDLE'])


db = SQLAlchemy()
login_manager = LoginManager()


#  The original werkzeug-url-converter cannot handle negative integers (e.g. asset/add/-1/1)
class IntegerConverter(OrigIntegerConvertor):
    regex = r'-?\d+'
    num_convert = int


# support custom filtering while logging
class MyLogFilter(logging.Filter):
    def filter(self, record):
        record.username = current_user.username if current_user and current_user.is_active else 'NONE'
        return True


# set up logging
LOG_FILENAME = os.path.join(sys.path[0], app_config[config_name].STATIC_PATH, f'log/{flask_app.config["LOG_FILE"]}.txt')
try:
    log_level = getattr(logging, app_config[config_name].LOG_LEVEL)
except:
    log_level = getattr(logging, 'INFO')
log.setLevel(log_level)
log.addFilter(MyLogFilter())
log_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=60 * 1024, backupCount=5)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(username)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

log.info(f"start {flask_app.config['SITE_NAME']}")

jsglue = JSGlue(flask_app)
db.app=flask_app  #  hack:-(
db.init_app(flask_app)

socketio = SocketIO(flask_app, async_mode=flask_app.config['SOCKETIO_ASYNC_MODE'], ping_timeout=10, ping_interval=5,
                    cors_allowed_origins=flask_app.config['SOCKETIO_CORS_ALLOWED_ORIGIN'])


def create_admin():
    from app.data.models import User
    find_admin = User.query.filter(User.username == 'admin').first()
    if not find_admin:
        admin = User(username='admin', password='admin', level=User.LEVEL.ADMIN, user_type=User.USER_TYPE.LOCAL)
        db.session.add(admin)
        db.session.commit()


flask_app.url_map.converters['int'] = IntegerConverter
login_manager.init_app(flask_app)
login_manager.login_message = 'Je moet aangemeld zijn om deze pagina te zien!'
login_manager.login_view = 'auth.login'

migrate = Migrate(flask_app, db)

# configure e-mailclient
email = Mail(flask_app)
send_emails = False

SCHEDULER_API_ENABLED = True
email_scheduler = APScheduler()
email_scheduler.init_app(flask_app)
email_scheduler.start()

if 'db' in sys.argv:
    from app.data import models
else:
    create_admin()  #  Only once

    # decorator to grant access to admins only
    def admin_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_at_least_admin:
                abort(403)
            return func(*args, **kwargs)
        return decorated_view


    # decorator to grant access to at least supervisors
    def supervisor_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_at_least_supervisor:
                abort(403)
            return func(*args, **kwargs)
        return decorated_view

    from app.presentation.view import auth, user, settings, guest, reservation, timeslot
    flask_app.register_blueprint(auth.auth)
    flask_app.register_blueprint(user.user)
    flask_app.register_blueprint(guest.guest)
    flask_app.register_blueprint(settings.settings)
    flask_app.register_blueprint(reservation.reservation)
    flask_app.register_blueprint(timeslot.timeslot)

    @flask_app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html', title='Forbidden'), 403

    @flask_app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html', title='Page Not Found'), 404

    @flask_app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html', title='Server Error'), 500

    @flask_app.route('/500')
    def error_500():
        abort(500)


