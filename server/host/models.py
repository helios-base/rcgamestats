import uuid
from datetime import datetime
from ..app import db


def generate_host_token():
    return str(uuid.uuid4())


class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    token = db.Column(db.String(36), unique=True, nullable=False,
                      default=generate_host_token)
    ip_v4_address = db.Column(db.String(16), default="")
    last_accessed_at = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    assigned_match_id = db.Column(db.Integer,
                                  db.ForeignKey("match.id",
                                                use_alter=True,
                                                name="fk_host_match_id"),
                                  nullable=True)

    # stats is a one-to-one relationship with HostStats
    stats = db.relationship("HostStats", back_populates="host", uselist=False, cascade="all, delete-orphan")

    def reset_stats(self):
        if self.stats:
            self.stats.total_runtime_synch_mode = 0.0
            self.stats.total_matches_synch_mode = 0
            self.stats.total_runtime_normal = 0.0
            self.stats.total_matches_normal = 0
            db.session.commit()


class HostStats(db.Model):
    __tablename__ = "host_stats"
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey("host.id"), unique=True, nullable=False)
    reset_count = db.Column(db.Integer, default=0)  # Number of times the assigned match has been reset
    decline_count = db.Column(db.Integer, default=0)
    total_runtime_synch_mode = db.Column(db.Float, default=0.0)
    total_matches_synch_mode = db.Column(db.Integer, default=0)
    total_runtime_normal = db.Column(db.Float, default=0.0)
    total_matches_normal = db.Column(db.Integer, default=0)

    host = db.relationship("Host", back_populates="stats")
