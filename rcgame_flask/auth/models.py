import secrets
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from rcgame_flask.app import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)
    scope = db.Column(db.String(255), nullable=True)

    @staticmethod
    def generate_api_key():
        return secrets.token_hex(32)
    
    def is_expired(self):
        return self.expires_at is not None and datetime.now(timezone.utc) > self.expires_at


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def generate_api_key():
    return secrets.token_hex(16)


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Decorator function to check for a valid API key in the request headers.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: JSON response with an error message and a 401 status code if the API key is invalid.
            Otherwise, it returns the decorated function's response.
        """
        api_key = request.headers.get("x-api-key")
        if api_key is None:
            return jsonify({"error": "Missing API key."}), 401
        record = APIKey.query.filter_by(key=api_key).first()
        if record is None:
            jsonify({"error": "Invalid or missing API key."}), 401
        if record.is_expired():
            return jsonify({"error": "API key has expired."}), 401
        return f(*args, **kwargs)

    return decorated_function
