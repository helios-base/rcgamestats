import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flask_login import login_required
from rcgame_flask.models import db, teams, group_matches, matches,certificate_key

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

@bp.route('/hosts')
@login_required
def show_hosts():
    host_list = certificate_key.query.all()
    return render_template('dbdisplay/hosts.html', host_list=host_list)

@bp.route('/update_stop_check/<int:key_id>', methods=['POST'])
@login_required
def update_stop_check(key_id):
    stop_check_value = request.form.get('stop_check')
    stop_check = True if stop_check_value == 'true' else False

    key = certificate_key.query.get(key_id)
    if key:
        key.stop_check = stop_check
        db.session.commit()
        host_list = certificate_key.query.all()
        return render_template('dbdisplay/hosts.html', host_list=host_list)