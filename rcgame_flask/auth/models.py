import secrets
from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from rcgame_flask.app import db, login_manager


class UserType(Enum):
    USER = 'user'
    ADMIN = 'admin'
    MASTER = 'master'


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    auth_provider = db.Column(db.String(50), nullable=False, default='local')  # local, google ...
    type = db.Column(db.Enum(UserType), default=UserType.USER)
    created_at = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    last_login_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def is_admin(self):
        return self.type == UserType.ADMIN or self.type == UserType.MASTER


class AllowedEmail(db.Model):
    __tablename__ = 'allowed_email'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    type = db.Column(db.Enum(UserType), default=UserType.USER)


class APIKey(db.Model):
    __tablename__ = 'api_key'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    expires_at = db.Column(db.DateTime, nullable=True)
    scope = db.Column(db.Enum(UserType), default=UserType.USER)

    user = db.relationship('User', backref=db.backref('api_keys', cascade='all, delete-orphan', lazy='dynamic'))

    @staticmethod
    def generate_api_key():
        return secrets.token_hex(16)

    def is_expired(self):
        return (self.expires_at is not None
                and datetime.now() > self.expires_at)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
