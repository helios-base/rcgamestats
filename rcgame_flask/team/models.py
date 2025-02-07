from rcgame_flask.app import db
from datetime import datetime


def current_datetime_str():
    return datetime.now().strftime('%Y%m%d-%H%M%S')


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    version = db.Column(db.String(32), nullable=False, default=current_datetime_str)
    synch_mode = db.Column(db.Boolean, nullable=False, default=True)
    archive_path = db.Column(db.String(512))
    memo = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
