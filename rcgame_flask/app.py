import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from authlib.integrations.flask_client import OAuth
from rcgame_flask.config import config

db = SQLAlchemy()
csrf = CSRFProtect()
# LoginManagerインスタンス
login_manager = LoginManager()
# 未認証のユーザーがアクセスしようとした際にリダイレクトされるエンドポイントを設定する
login_manager.login_view = "auth.login"
# ログインが必要なページにアクセスしようとした際に表示されるメッセージ
login_manager.login_message = "Please log in to access this page."


def init_logging(app):
    app.logger.handlers = []  # clear the default handler

    log_dir = os.path.join(app.static_folder, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'server.log')

    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=10)
    formatter = logging.Formatter(
        # '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        '%(asctime)s %(levelname)s: %(message)s'
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Server startup')


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # app.config.from_mapping(
    #     SECRET_KEY='xxxxxxxx',
    #     SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'rcgame_flask.sqlite'),
    #     SQLALCHEMY_TRACK_MODIFICATIONS=False,
    #     WTF_CSRF_ENABLED=True,
    #     WTF_CSRF_SECRET_KEY='xxxxxxxx',
    #     )
    app.config.from_object(config)

    if test_config is not None:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    init_logging(app)

    from . import create_db
    create_db.init_app(app)

    Migrate(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)  # register the login_manager with the app

    if app.config['GOOGLE_OAUTH_CLIENT_ID'] and app.config['GOOGLE_OAUTH_CLIENT_SECRET']:
        oauth = OAuth(app)
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
            client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
            authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
            authorize_params=None,
            access_token_url='https://accounts.google.com/o/oauth2/token',
            access_token_params=None,
            refresh_token_url=None,
            client_kwargs={'scope': 'email'},
        )
        app.oauth = oauth
        app.logger.info('Google OAuth enabled')

    from rcgame_flask.auth import views as auth_views
    app.register_blueprint(auth_views.auth, url_prefix='/auth')

    # from rcgame_flask.group import views as group_views
    # app.register_blueprint(group_views.group, url_prefix='/group')
    from rcgame_flask.group import group
    app.register_blueprint(group, url_prefix='/group')

    from rcgame_flask.team import views as team_views
    app.register_blueprint(team_views.team, url_prefix='/team')

    from rcgame_flask.host import views as host_views
    app.register_blueprint(host_views.host, url_prefix='/host')

    # set Enums as global variables for Jinja templates
    from rcgame_flask.auth.models import UserType
    from rcgame_flask.group.models import GroupStatus
    from rcgame_flask.group.models import MatchStatus
    app.jinja_env.globals['UserType'] = UserType
    app.jinja_env.globals['GroupStatus'] = GroupStatus
    app.jinja_env.globals['MatchStatus'] = MatchStatus

    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')

    @app.template_filter('basename')
    def basename(path):
        return os.path.basename(path)

    return app


app = create_app()
