from rcgame_flask.app import db


# TODO: log_direcotry_nameをMatchからGroupへ移動させる

class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    left_team = db.Column(db.String(30), nullable=False)
    right_team = db.Column(db.String(30), nullable=False)
    number_of_matches = db.Column(db.Integer, nullable=False)
    memo = db.Column(db.Text)


class Match(db.Model):
    __tablename__ = 'match'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    group_index = db.Column(db.Integer)
    host_name = db.Column(db.String(30))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    left_team = db.Column(db.String(30))
    right_team = db.Column(db.String(30))
    left_score = db.Column(db.Integer)
    right_score = db.Column(db.Integer)
    processed = db.Column(db.String(15), default='unexecuted')
    log_file_name = db.Column(db.String(255))
