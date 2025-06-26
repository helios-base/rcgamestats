from datetime import datetime
from enum import Enum
from ..app import db


def current_datetime_str():
    return datetime.now().strftime('%Y%m%d-%H%M%S')


class TeamReviewStatus(Enum):
    NORMAL = 'normal'
    REJECTED = 'rejected'
    UNDER_REVIEW = 'under_review'
    APPROVED = 'approved'


class Team(db.Model):
    __tablename__ = 'team'
    __table_args__ = (
        db.UniqueConstraint('name', 'version', name='unique_name_version'),
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    version = db.Column(db.String(32), nullable=False, default=current_datetime_str)
    synch_mode = db.Column(db.Boolean, nullable=False, default=True)
    archive_path = db.Column(db.String(512), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    review_status = db.Column(db.Enum(TeamReviewStatus), nullable=False, default=TeamReviewStatus.NORMAL)
