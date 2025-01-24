import functools
import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flask_login import login_required
from rcgame_flask.models import db, teams, group_matches, matches,certificate_key
from flask import current_app, jsonify, render_template

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

@bp.route('/match_log/<int:match_id>', methods=['GET'])
@login_required
def match_log(match_id):
    match = matches.query.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    log_directory_name = match.log_directory_name
    logs_dir = os.path.join(current_app.static_folder, 'logs')
    log_dir_path = os.path.join(logs_dir, log_directory_name)

    if not os.path.exists(log_dir_path):
        return jsonify({"error": "Log directory not found"}), 404

    log_files = [f for f in os.listdir(log_dir_path) if match.log_file in f]

    if not log_files:
        return jsonify({"error": "No matching log files found"}), 404

    return render_template('dbdisplay/log_file.html', log_files=log_files, log_directory=log_directory_name)

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