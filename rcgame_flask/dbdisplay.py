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

#team関係の表示
@bp.route('/teams')
@login_required
def show_teams():
    team_list = teams.query.all()
    return render_template('dbdisplay/teams.html', teams=team_list)

#group_matches関係の表示
@bp.route('/group_matches')
@login_required
def show_group_matches():
    match_list = group_matches.query.all()
    return render_template('dbdisplay/group_matches.html', matches=match_list)

#group_matchesのレコード削除
@bp.route('/delete_match/<int:group_id>', methods=['POST'])
@login_required
def delete_match(group_id):
    matches_to_delete = matches.query.filter_by(group_id=group_id).all()
    group_match_to_delete = group_matches.query.get(group_id)
    
    if matches_to_delete:
        for match in matches_to_delete:
            db.session.delete(match)
    
    if group_match_to_delete:
        group_name = group_match_to_delete.group_name
        db.session.delete(group_match_to_delete)
    
    db.session.commit()
    flash(f'{group_name}は削除されました。')
    
    return redirect(url_for('dbdisplay.show_group_matches'))

@bp.route('/group_matches/<int:group_id>')
@login_required
def show_group_matches_detail(group_id):
    match_list = matches.query.filter_by(group_id=group_id).all()
    return render_template('dbdisplay/group_matches_detail.html', matches=match_list)

@bp.route('/group_log_files/<int:group_id>', methods=['GET'])
@login_required
def show_group_log_files(group_id):
    matches_in_group = matches.query.filter_by(group_id=group_id).all()
    log_files = []
    log_directory = None

    for match in matches_in_group:
        log_directory = match.log_directory_name
        logs_dir = os.path.join(current_app.static_folder, 'logs')
        log_dir_path = os.path.join(logs_dir, log_directory)

        if os.path.exists(log_dir_path):
            log_files.extend([f for f in os.listdir(log_dir_path) if match.log_file_name in f])

    if not log_files:
        return jsonify({"error": "No matching log files found"}), 404

    return render_template('dbdisplay/log_file.html', log_files=log_files, log_directory=log_directory)

@bp.route('/all_log_files', methods=['GET'])
@login_required
def show_all_log_files():
    logs_dir = os.path.join(current_app.static_folder, 'logs')
    all_log_files = []

    for root, dirs, files in os.walk(logs_dir):
        for file in files:
            all_log_files.append(os.path.relpath(os.path.join(root, file), current_app.static_folder))

    if not all_log_files:
        return jsonify({"error": "No log files found"}), 404

    # ファイル名のみを取得
    all_log_files = sorted([os.path.basename(f) for f in all_log_files], key=lambda x: int(x.split('_')[0]))

    return render_template('dbdisplay/all_log_files.html', log_files=all_log_files)


#matches関係の表示
@bp.route('/matches')
@login_required
def show_matches():
    match_list = matches.query.all()
    return render_template('dbdisplay/matches.html', matches=match_list)

@bp.route('/reset_match/<int:match_id>', methods=['GET'])
@login_required
def reset_match(match_id):
    match = matches.query.get(match_id)
    if match and match.processed == 'in progress':
        match.host_name = None
        match.start_time = None
        match.processed = 'unexecuted'
        db.session.commit()
    
    return redirect(url_for('dbdisplay.show_matches'))

@bp.route('/match_log/<int:match_id>', methods=['GET'])
@login_required
def match_log(match_id):
    match = matches.query.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    log_file_name = match.log_file_name
    logs_dir = os.path.join(current_app.static_folder, 'logs')
    log_dir_path = os.path.join(logs_dir, match.log_directory_name)

    if not os.path.exists(log_dir_path):
        return jsonify({"error": "Log directory not found"}), 404

    log_files = [f for f in os.listdir(log_dir_path) if log_file_name in f]

    if not log_files:
        return jsonify({"error": "No matching log files found"}), 404

    return render_template('dbdisplay/log_file.html', log_files=log_files, log_directory=match.log_directory_name)


#certificate_key関係の表示
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