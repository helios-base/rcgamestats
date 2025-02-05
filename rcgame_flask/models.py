from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from rcgame_flask.app import db, login_manager


class user(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    def set_password(self, password):
        self.password = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password, password)

class group_matches(db.Model):
    group_id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(255), unique=True)
    group_time = db.Column(db.DateTime)
    left_team = db.Column(db.String(30))
    right_team = db.Column(db.String(30))
    group_memo = db.Column(db.Text)
    game_count = db.Column(db.Integer)
    executed_count = db.Column(db.Integer, default=0)

class hosts(db.Model):
    host_id = db.Column(db.Integer, primary_key=True)
    host_name = db.Column(db.String(30))
    IP = db.Column(db.String(12))
    is_standby = db.Column(db.String(10))

class certificate_key(db.Model):
    key_id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(32), unique=True, nullable=False)
    stop_check = db.Column(db.Boolean, default=False, nullable=False)

class matches(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group_matches.group_id'))
    match_index = db.Column(db.Integer)
    host_name = db.Column(db.String(30))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    left_team = db.Column(db.String(30))
    right_team = db.Column(db.String(30))
    left_score = db.Column(db.Integer)
    right_score = db.Column(db.Integer)
    processed = db.Column(db.String(15), default='unexecuted')
    log_directory_name = db.Column(db.String(255))
    log_file_name = db.Column(db.String(255))
    log_file = db.Column(db.String(255))

class teams(db.Model):
    team_id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(255), unique=True)
    acceleration = db.Column(db.String(5))
    filepass = db.Column(db.String(50))
    team_memo = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return user.query.get(int(user_id))