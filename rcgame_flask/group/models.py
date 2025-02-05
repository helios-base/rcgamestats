from rcgame_flask.app import db


# TODO: log_direcotry_nameをMatchからGroupへ移動させる

class Group(db.Model):
    group_id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(255), unique=True)
    group_time = db.Column(db.DateTime)
    left_team = db.Column(db.String(30))
    right_team = db.Column(db.String(30))
    group_memo = db.Column(db.Text)
    game_count = db.Column(db.Integer)
    executed_count = db.Column(db.Integer, default=0)


class Match(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'))
    match_index = db.Column(db.Integer)
    host_name = db.Column(db.String(30))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    left_team = db.Column(db.String(30))
    right_team = db.Column(db.String(30))
    left_score = db.Column(db.Integer)
    right_score = db.Column(db.Integer)
    processed = db.Column(db.String(15), default='unexecuted')
    log_directory_name = db.Column(db.String(255))
    log_file_name = db.Column(db.String(255))
    log_file = db.Column(db.String(255))
