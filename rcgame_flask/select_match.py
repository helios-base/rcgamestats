import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from rcgame_flask.db import get_db

bp = Blueprint('select_match', __name__, url_prefix='/select_match')

@bp.route('/teamselect', methods=('GET','POST'))
def select_team():
    db = get_db()
    teams = db.execute('SELECT team_name FROM teams').fetchall()
    
    if request.method == 'POST':
        select_team1 = request.form['team_name1']
        select_team2 = request.form['team_name2']
        match_count = request.form['match_count']
        group_memo = request.form['group_memo']
        db = get_db()
        error = None

        if not select_team1:
            error = 'team serect is required.'
        elif not select_team2:
            error = 'team select is required.'
        elif select_team1 == select_team2:
            error = '「Team1」と「Team2」が重複しています.'

        if error is None:
            db.execute(
            "INSERT INTO group_matches (group_time,left_team, right_team, game_count, group_memo) VALUES (datetime('now'),?, ?, ?, ?)",
            (select_team1, select_team2, match_count, group_memo)
            )
            db.commit()
            return redirect(url_for("dbdisplay.show_group_matches"))

        flash(error)
        
    return render_template('select_match/select_team.html', teams=teams)
