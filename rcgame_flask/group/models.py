from enum import Enum
from rcgame_flask.app import db


class GroupStatus(Enum):
    NORMAL = 'normal'
    REJECTED = 'rejected'
    UNDER_REVIEW = 'under_review'
    APPROVED = 'approved'


class MatchStatus(Enum):
    UNEXECUTED = 'unexecuted'
    IN_PROGRESS = 'in progress'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'


class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    left_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    right_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.Enum(GroupStatus), default=GroupStatus.NORMAL)

    left_team = db.relationship('Team', foreign_keys=[left_team_id])
    right_team = db.relationship('Team', foreign_keys=[right_team_id])


class Match(db.Model):
    __tablename__ = 'match'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    group_index = db.Column(db.Integer)
    host_name = db.Column(db.String(30))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    left_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    right_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    left_score = db.Column(db.Integer)
    right_score = db.Column(db.Integer)
    processed = db.Column(db.Enum(MatchStatus), default=MatchStatus.UNEXECUTED)
    log_file_name = db.Column(db.String(255))
    token = db.Column(db.String(16))

    # group = db.relationship('Group', foreign_keys=[group_id])
    group = db.relationship('Group', backref=db.backref('matches', lazy='dynamic'))
    left_team = db.relationship('Team', foreign_keys=[left_team_id])
    right_team = db.relationship('Team', foreign_keys=[right_team_id])
