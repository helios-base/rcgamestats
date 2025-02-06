import os
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
csrf = CSRFProtect()
# LoginManagerインスタンス
login_manager = LoginManager()
# 未認証のユーザーがアクセスしようとした際にリダイレクトされるエンドポイントを設定する
login_manager.login_view = "auth.login"
# ログインが必要なページにアクセスしようとした際に表示されるメッセージ
login_manager.login_message = "Please log in to access this page."


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'rcgame_flask.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_SECRET_KEY='kwjer283n2k3gpiue9vrdfagb',
        )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import create_db
    create_db.init_app(app)

    Migrate(app, db)

    csrf.init_app(app)

    # LoginManagerとFlaskとの紐づけ
    login_manager.init_app(app)

    from rcgame_flask.auth import views as auth_views
    app.register_blueprint(auth_views.auth, url_prefix='/auth')
    
    from rcgame_flask.group import views as group_views
    app.register_blueprint(group_views.group, url_prefix='/group')
    
    from rcgame_flask.team import views as team_views
    app.register_blueprint(team_views.team, url_prefix='/team')

    from rcgame_flask.host import views as host_views
    app.register_blueprint(host_views.host, url_prefix='/host')

    from . import dbdisplay
    app.register_blueprint(dbdisplay.bp)

    from . import communication
    app.register_blueprint(communication.bp)

    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')

    return app


app = create_app()
