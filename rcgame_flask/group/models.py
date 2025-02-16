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


class GroupStats():
    """
    GroupStats class is used to store the statistics of a group.
    """
    def __init__(self, group_id):
        self.group_id = group_id
        self.group = Group.query.get(group_id)
        self.completed_count = 0
        self.left_win = 0
        self.right_win = 0
        self.draw = 0
        self.left_goals = 0
        self.right_goals = 0
        self.left_win_rate = 0.0
        self.right_win_rate = 0.0
        self.draw_rate = 0.0
        self.left_ave_goal = 0.0
        self.right_ave_goal = 0.0
        self.left_max_goal = 0
        self.right_max_goal = 0
        self.left_scored_count = 0
        self.right_scored_count = 0
        self.left_score_rate = 0.0
        self.right_score_rate = 0.0
        self.left_score_counts = { i: 0 for i in range(11) }
        self.right_score_counts = { i: 0 for i in range(11) }
        self.host_counts = {}

        self.__calculate()

    def __calculate(self):
        """
        Calculate the statistics of the group.
        """
        if self.group is None:
            return
        matches = Match.query.filter_by(group_id=self.group_id, processed=MatchStatus.COMPLETED).all()
        self.completed_count = len(matches)
        left_max_score = 10
        right_max_score = 10
        for match in matches:
            if match.left_score > match.right_score:
                self.left_win += 1
            elif match.left_score < match.right_score:
                self.right_win += 1
            else:
                self.draw += 1
            self.left_goals += match.left_score
            self.right_goals += match.right_score
            self.left_scored_count += 1 if match.left_score > 0 else 0
            self.right_scored_count += 1 if match.right_score > 0 else 0
            self.left_max_goal = max(self.left_max_goal, match.left_score)
            self.right_max_goal = max(self.right_max_goal, match.right_score)

            if match.left_score not in self.left_score_counts:
                if match.left_score > left_max_score:
                    for i in range(left_max_score+1, match.left_score+1):
                        self.left_score_counts[i] = 0
                    left_max_score = match.left_score
                self.left_score_counts[match.left_score] = 1
            else:
                self.left_score_counts[match.left_score] += 1
            
            if match.right_score not in self.right_score_counts:
                if match.right_score > right_max_score:
                    for i in range(right_max_score+1, match.right_score+1):
                        self.right_score_counts[i] = 0
                    right_max_score = match.right_score
                self.right_score_counts[match.right_score] = 1
            else:
                self.right_score_counts[match.right_score] += 1

            if match.host_name not in self.host_counts:
                self.host_counts[match.host_name] = 1
            else:
                self.host_counts[match.host_name] += 1

        if self.completed_count > 0:
            self.left_win_rate = self.left_win / self.completed_count
            self.right_win_rate = self.right_win / self.completed_count
            self.draw_rate = self.draw / self.completed_count
            self.left_ave_goals = self.left_goals / self.completed_count
            self.right_ave_goals = self.right_goals / self.completed_count
            self.left_score_rate = self.left_scored_count / self.completed_count
            self.right_score_rate = self.right_scored_count / self.completed_count
