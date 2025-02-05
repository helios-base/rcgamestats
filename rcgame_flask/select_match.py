import functools
from datetime import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flask_login import login_required
from werkzeug.security import check_password_hash, generate_password_hash
from rcgame_flask.models import db, teams
from rcgame_flask.group.models import Group, Match
from rcgame_flask.googlesheet import googlesheet

bp = Blueprint('select_match', __name__, url_prefix='/select_match')

@bp.route('/select_team', methods=('GET', 'POST'))
@login_required
def select_team():
    team_list = teams.query.all()
    
    if request.method == 'POST':
        select_team1 = request.form['team_name1']
        select_team2 = request.form['team_name2']
        match_count = int(request.form['match_count'])
        group_memo = request.form['group_memo']
        error = None
        
        if not select_team1:
            error = 'team select is required.'
        elif not select_team2:
            error = 'team select is required.'
        elif select_team1 == select_team2:
            error = '「Team1」と「Team2」が重複しています.'

        if error is None:
            now = datetime.now().replace(microsecond=0)
            timestamp = now.strftime("%m%d%H%M")
            group_name = timestamp + "-" + select_team1 + "-" + select_team2
            group_match = Group(
                group_name=group_name,
                group_time=now,
                left_team=select_team1,
                right_team=select_team2,
                game_count=match_count,
                group_memo=group_memo
            )
            db.session.add(group_match)
            db.session.commit()

            for i in range(match_count):
                match = Match(
                    match_index=i+1,
                    group_id=group_match.group_id,
                    left_team=select_team1,
                    right_team=select_team2
                )
                db.session.add(match)
            db.session.commit()

            if googlesheet.get_or_create_group_sheet(group_name, now, select_team1, select_team2, group_memo) is None:
                flash('Error: Failed to create a group sheet for ' + group_name)
            return redirect(url_for("dbdisplay.show_group_matches"))

        flash(error)

    return render_template('select_match/select_team.html', teams=team_list)