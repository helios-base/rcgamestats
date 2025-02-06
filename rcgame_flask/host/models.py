from rcgame_flask.app import db


class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    IP = db.Column(db.String(12))
    is_standby = db.Column(db.String(10))
