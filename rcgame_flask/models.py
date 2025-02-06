from rcgame_flask.app import db

class hosts(db.Model):
    host_id = db.Column(db.Integer, primary_key=True)
    host_name = db.Column(db.String(30))
    IP = db.Column(db.String(12))
    is_standby = db.Column(db.String(10))


