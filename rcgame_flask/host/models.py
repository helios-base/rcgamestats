from rcgame_flask.app import db


class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False, default="unknown")
    ip_v4_address = db.Column(db.String(16), default="")
    last_accessed_at = db.Column(db.DateTime)
    assigned_match_id = db.Column(db.Integer, db.ForeignKey("match.id"))
    decline_count = db.Column(db.Integer, default=0)
    total_runtime_synch_mode = db.Column(db.Float, default=0.0)
    total_matches_synch_mode = db.Column(db.Integer, default=0)
    total_runtime_normal = db.Column(db.Float, default=0.0)
    total_matches_normal = db.Column(db.Integer, default=0)

    assigned_match = db.relationship(
        "Match",
        foreign_keys=[assigned_match_id],
        lazy="joined",  # simultenous query with Host
        uselist=False)  # only 1 connection
