import numpy as np
import scipy.stats as stats
from collections import Counter
from datetime import datetime
from enum import Enum
from ..team.models import TeamReviewStatus
from ..app import db


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
    updated_at = db.Column(db.DateTime)
    left_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    right_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    left_team = db.relationship('Team', foreign_keys=[left_team_id])
    right_team = db.relationship('Team', foreign_keys=[right_team_id])

    def completed_count(self):
        return Match.query.filter_by(group_id=self.id, processed=MatchStatus.COMPLETED).count()

    def to_simple_json(self):
        json = {
            'group_id': self.id,
            'name': self.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'left_team_id': self.left_team.id,
            'right_team_id': self.right_team.id,
            'left_team': self.left_team.name,
            'right_team': self.right_team.name,
            'completed_count': self.stats.completed_count if self.stats else 0,
            'left_win': self.stats.left_win if self.stats else 0,
            'right_win': self.stats.right_win if self.stats else 0,
            'draw': self.stats.draw if self.stats else 0,
            'left_win_rate': self.stats.left_win_rate if self.stats else 0,
            'right_win_rate': self.stats.right_win_rate if self.stats else 0,
            'draw_rate': self.stats.draw_rate if self.stats else 0,
            'left_sum_of_scores': self.stats.left_sum_of_scores if self.stats else 0,
            'right_sum_of_scores': self.stats.right_sum_of_scores if self.stats else 0,
            'left_max_score': self.stats.left_max_score if self.stats else 0,
            'right_max_score': self.stats.right_max_score if self.stats else 0,
            'left_scored_games': self.stats.left_scored_games if self.stats else 0,
            'right_scored_games': self.stats.right_scored_games if self.stats else 0,
            'left_scored_games_rate': self.stats.left_scored_games_rate if self.stats else 0,
            'right_scored_games_rate': self.stats.right_scored_games_rate if self.stats else 0,
            'left_mean_score': self.stats.left_mean_score if self.stats else 0,
            'right_mean_score': self.stats.right_mean_score if self.stats else 0,
            'left_score_ci': [self.stats.left_score_confidence_interval_lower, self.stats.left_score_confidence_interval_upper] if self.stats else [0, 0],
            'right_score_ci': [self.stats.right_score_confidence_interval_lower, self.stats.right_score_confidence_interval_upper] if self.stats else [0, 0],
            'left_score_counts': self.stats.left_score_counts if self.stats else {"0": 0},
            'right_score_counts': self.stats.right_score_counts if self.stats else {"0": 0},
        }

        if self.left_team.review_status != TeamReviewStatus.NORMAL:
            json['left_status'] = self.left_team.review_status.value
        if self.right_team.review_status != TeamReviewStatus.NORMAL:
            json['right_status'] = self.right_team.review_status.value
        return json

class Match(db.Model):
    __tablename__ = 'match'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    index = db.Column(db.Integer)
    host_id = db.Column(db.Integer, db.ForeignKey('host.id'))
    host_name = db.Column(db.String(30))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    left_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    right_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    left_score = db.Column(db.Integer)
    right_score = db.Column(db.Integer)
    processed = db.Column(db.Enum(MatchStatus), name="match_status_enum", default=MatchStatus.UNEXECUTED)
    log_file_name = db.Column(db.String(255))
    token = db.Column(db.String(16))

    group = db.relationship('Group', backref=db.backref('matches', cascade='all, delete-orphan', lazy='dynamic'))
    left_team = db.relationship('Team', foreign_keys=[left_team_id])
    right_team = db.relationship('Team', foreign_keys=[right_team_id])
    host = db.relationship('Host', foreign_keys=[host_id])

    def reset_assignment(self):
        self.host_id = None
        self.host_name = None
        self.start_time = None
        self.end_time = None
        self.left_score = None
        self.right_score = None
        self.processed = MatchStatus.UNEXECUTED
        self.log_file_name = None
        self.token = None


class GroupStats(db.Model):
    __tablename__ = 'group_stats'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), unique=True, nullable=False)
    updated_at = db.Column(db.DateTime)
    completed_count = db.Column(db.Integer)
    left_win = db.Column(db.Integer)
    right_win = db.Column(db.Integer)
    draw = db.Column(db.Integer)
    left_sum_of_scores = db.Column(db.Integer)
    right_sum_of_scores = db.Column(db.Integer)
    left_win_rate = db.Column(db.Float)
    right_win_rate = db.Column(db.Float)
    draw_rate = db.Column(db.Float)
    left_max_score = db.Column(db.Integer)
    right_max_score = db.Column(db.Integer)
    left_scored_games = db.Column(db.Integer)
    right_scored_games = db.Column(db.Integer)
    left_scored_games_rate = db.Column(db.Float)
    right_scored_games_rate = db.Column(db.Float)
    left_score_counts = db.Column(db.JSON)
    right_score_counts = db.Column(db.JSON)
    left_mean_score = db.Column(db.Float)
    right_mean_score = db.Column(db.Float)
    left_score_confidence_interval_lower = db.Column(db.Float)
    left_score_confidence_interval_upper = db.Column(db.Float)
    right_score_confidence_interval_lower = db.Column(db.Float)
    right_score_confidence_interval_upper = db.Column(db.Float)
    host_counts = db.Column(db.JSON)

    group = db.relationship('Group', backref=db.backref('stats', cascade='all, delete-orphan', uselist=False, lazy='joined'))

    def __init__(self, group_id):
        self.group_id = group_id
        self.completed_count = 0
        self.left_win = 0
        self.right_win = 0
        self.draw = 0
        self.left_sum_of_scores = 0
        self.right_sum_of_scores = 0
        self.left_win_rate = 0.0
        self.right_win_rate = 0.0
        self.draw_rate = 0.0
        self.left_max_score = 0
        self.right_max_score = 0
        self.left_scored_games = 0
        self.right_scored_games = 0
        self.left_scored_games_rate = 0.0
        self.right_scored_games_rate = 0.0
        self.left_score_counts = {str(i): 0 for i in range(5)}
        self.right_score_counts = {str(i): 0 for i in range(5)}
        self.left_mean_score = 0.0
        self.right_mean_score = 0.0
        self.left_score_confidence_interval_lower = 0.0
        self.left_score_confidence_interval_upper = 0.0
        self.right_score_confidence_interval_lower = 0.0
        self.right_score_confidence_interval_upper = 0.0
        self.host_counts = {}

    def __compute_confidence_interval(self, data, mean, confidence=0.95):
        if len(data) < 2:
            return mean, mean

        se = stats.sem(data)
        if se == 0:
            return mean, mean

        return stats.t.interval(confidence, len(data) - 1, loc=mean, scale=se)

    def update(self):
        """
        Calculate the statistics of the group.
        """
        matches = Match.query.filter_by(group_id=self.group_id, processed=MatchStatus.COMPLETED).all()
        self.completed_count = len(matches)

        if self.completed_count == 0:
            return

        left_scores = np.array([match.left_score for match in matches if match.left_score is not None and match.left_score >= 0])
        right_scores = np.array([match.right_score for match in matches if match.right_score is not None and match.right_score >= 0])

        self.left_win = int(np.sum(left_scores > right_scores))
        self.right_win = int(np.sum(left_scores < right_scores))
        self.draw = int(np.sum(left_scores == right_scores))
        self.left_sum_of_scores = int(np.sum(left_scores))
        self.right_sum_of_scores = int(np.sum(right_scores))
        self.left_win_rate = self.left_win / self.completed_count
        self.right_win_rate = self.right_win / self.completed_count
        self.draw_rate = self.draw / self.completed_count
        self.left_max_score = int(np.max(left_scores))
        self.right_max_score = int(np.max(right_scores))
        self.left_scored_games = int(np.sum(left_scores > 0))
        self.right_scored_games = int(np.sum(right_scores > 0))
        self.left_scored_games_rate = self.left_scored_games / self.completed_count
        self.right_scored_games_rate = self.right_scored_games / self.completed_count
        self.left_score_counts = {str(i): int(count) for i, count in enumerate(np.bincount(left_scores, minlength=6))}
        self.right_score_counts = {str(i): int(count) for i, count in enumerate(np.bincount(right_scores, minlength=6))}
        self.left_mean_score = float(np.mean(left_scores))
        self.right_mean_score = float(np.mean(right_scores))
        # self.host_counts = dict(Counter([match.host_name for match in matches if match.host_name is not None]))
        self.host_counts = dict(Counter(f"{match.host_name} ({match.host_id})" for match in matches))

        if self.completed_count > 1:
            ci_left = self.__compute_confidence_interval(left_scores, self.left_mean_score)
            self.left_score_confidence_interval_lower = max(0, float(ci_left[0]))
            self.left_score_confidence_interval_upper = float(ci_left[1])
            ci_right = self.__compute_confidence_interval(right_scores, self.right_mean_score)
            self.right_score_confidence_interval_lower = max(0, float(ci_right[0]))
            self.right_score_confidence_interval_upper = float(ci_right[1])

        self.updated_at = datetime.now().replace(microsecond=0)
