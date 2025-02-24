import uuid
from rcgame_flask.app import db


def generate_host_token():
    return str(uuid.uuid4())


class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    token = db.Column(db.String(36), unique=True, nullable=False, default=generate_host_token)
    ip_v4_address = db.Column(db.String(16), default="")
    last_accessed_at = db.Column(db.DateTime)
    assigned_match_id = db.Column(db.Integer, db.ForeignKey("match.id"))
    decline_count = db.Column(db.Integer, default=0)
    total_runtime_synch_mode = db.Column(db.Float, default=0.0)
    total_matches_synch_mode = db.Column(db.Integer, default=0)
    total_runtime_normal = db.Column(db.Float, default=0.0)
    total_matches_normal = db.Column(db.Integer, default=0)

    def reset_stats(self):
        self.decline_count = 0
        self.total_runtime_synch_mode = 0.0
        self.total_matches_synch_mode = 0
        self.total_runtime_normal = 0.0
        self.total_matches_normal = 0
        db.session.commit()