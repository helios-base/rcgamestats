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

    log_directory = os.path.join(current_app.static_folder, 'logs', match.log_directory_name)
    log_file_path = os.path.join(log_directory, match.log_file)

    if not os.path.exists(log_file_path):
        return jsonify({"error": "Log file not found"}), 404

    if os.path.isdir(log_file_path):
        # ディレクトリ内のファイルをリスト表示
        log_files = os.listdir(log_file_path)
        return render_template('dbdisplay/log_file.html', log_files=log_files, log_file_path=log_file_path)
    else:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            log_content = file.read()
        return render_template('dbdisplay/log_file.html', log_content=log_content)

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