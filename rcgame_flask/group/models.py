from rcgame_flask.app import db


class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    left_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    right_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    number_of_matches = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    is_archived = db.Column(db.Boolean, default=False)

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
    processed = db.Column(db.String(15), default='unexecuted')
    log_file_name = db.Column(db.String(255))
    token = db.Column(db.String(16))

    group = db.relationship('Group', foreign_keys=[group_id])
    # group = db.relationship('Group', backref=db.backref('matches', lazy='dynamic'))
    left_team = db.relationship('Team', foreign_keys=[left_team_id])
    right_team = db.relationship('Team', foreign_keys=[right_team_id])
