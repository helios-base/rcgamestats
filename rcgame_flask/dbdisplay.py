import functools
import os
import shutil
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flask_login import login_required
from rcgame_flask.models import db, teams, certificate_key
from rcgame_flask.group.models import Group, Match
from flask import current_app, jsonify, render_template
from rcgame_flask.googlesheet import googlesheet

bp = Blueprint('dbdisplay', __name__, url_prefix='/dbdisplay')

#team関係の表示
@bp.route('/teams')
@login_required
def show_teams():
    team_list = teams.query.all()
    return render_template('dbdisplay/teams.html', teams=team_list)


@bp.route('/upload_to_google_sheet/<int:group_id>', methods=['POST'])
@login_required
def upload_to_google_sheet(group_id):
    group = Group.query.get(group_id)
    if group is None:
        flash(f'ID:{group_id} のグループを取得できませんでした。')
        return redirect(url_for('dbdisplay.group_matches'))
    
    group_name = group.group_name
    if group_name is None:
        flash(f'ID:{group_id} のグループ名を取得できませんでした。')
        return redirect(url_for('dbdisplay.group_matches'))
    
    group_time = group.group_time
    left_team = group.left_team
    right_team = group.right_team
    memo = group.group_memo

    print(f'(upload_to_google_sheet) group_name: {group_name}, time: {group_time}, left_team: {left_team}, right_team: {right_team}, memo: [{memo}]')
    # データベースから指定されたグループIDのマッチデータを取得
    match_records = Match.query.filter_by(group_id=group_id).all()
    
    # Googleスプレッドシートにデータをアップロード
    if googlesheet.upload_group_results(group_name, group_time, left_team, right_team, memo, match_records):
        flash('Succeeded to upload the group results to the Google Spreadsheet.')
    else:
        flash('Failed to upload the group results to the Google Spreadsheet.')

    return redirect(url_for('group.show_group_matches', group_id=group_id))


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