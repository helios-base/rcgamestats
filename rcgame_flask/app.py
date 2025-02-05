import os
from flask import Flask
from flask_migrate import Migrate
from rcgame_flask.models import db, user
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


csrf = CSRFProtect()


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

    # LoginManagerインスタンス
    login_manager = LoginManager()
    # LoginManagerとFlaskとの紐づけ
    login_manager.init_app(app)
    # 未認証のユーザーがアクセスしようとした際に
    # リダイレクトされる関数名を設定する
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return user.query.get(int(user_id))

    from rcgame_flask.auth import views as auth_views
    app.register_blueprint(auth_views.auth, url_prefix='/auth')
    
    from . import list
    app.register_blueprint(list.bp)
    app.add_url_rule('/', endpoint='index')

    from . import select_match
    app.register_blueprint(select_match.bp)

    from . import dbdisplay
    app.register_blueprint(dbdisplay.bp)

    from . import communication
    app.register_blueprint(communication.bp)

    return app


app = create_app()
