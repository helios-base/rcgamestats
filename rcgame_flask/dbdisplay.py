import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from rcgame_flask.auth import login_required
from rcgame_flask.models import db, teams, group_matches, matches

bp = Blueprint('dbdisplay', __name__, url_prefix='/dbdisplay')

@bp.route('/teams')
@login_required
def show_teams():
    team_list = teams.query.all()
    return render_template('dbdisplay/teams.html', teams=team_list)

@bp.route('/group_matches')
@login_required
def show_group_matches():
    match_list = group_matches.query.all()
    return render_template('dbdisplay/group_matches.html', matches=match_list)

@bp.route('/matches')
@login_required
def show_matches():
    match_list = matches.query.all()
    return render_template('dbdisplay/matches.html', matches=match_list)