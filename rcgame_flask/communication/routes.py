import os
import re
import secrets
from flask import jsonify, request
from rcgame_flask.communication import bp
from rcgame_flask.app import db, csrf
from rcgame_flask.auth.models import APIKey, require_api_key
from rcgame_flask.group.models import Group, Match
from datetime import datetime
from functools import wraps

def log_file_name(group_id, match_index, host_name,left_team,right_team):
    match_index = str(match_index).zfill(5)
    group_id = str(group_id).zfill(5)
    return f"{group_id}_{match_index}_{left_team}_{right_team}_{host_name}"

def generate_api_key():
   return secrets.token_hex(16)


@bp.route("/create_user/<host_name>", methods=["POST"])
def create_user(host_name):
    existing_user = APIKey.query.filter_by(host_name=host_name).first()
    if existing_user:
        return {'error': 'host_name already exists'}, 400

    api_key = generate_api_key()
    new_user = APIKey(key=api_key)
    db.session.add(new_user)
    db.session.commit()
    return {'host_name': host_name, 'api_key': api_key}

@bp.route("/callback", methods=["POST"])
@require_api_key
def callback():
    print(request.data.decode())
    return jsonify({"kekka": "受け取ったよ!"})

@bp.route("/api", methods=["POST"])
@csrf.exempt
@require_api_key
def api():
    csrf_token = request.headers.get('X-CSRFToken')
    print("call api: CRSF Token:", csrf_token)
    data = request.get_json()
    host_name = data.get("host_name")
    api_key = data.get("api_key")

    if not host_name or not api_key:
        return jsonify({"error": "No hostname or API Key."}), 400
    
    cert_key = APIKey.query.filter_by(key=api_key).first()
    if not cert_key:
        return jsonify({"error": "Invalid API Key"}), 400

    match = Match.query.filter_by(processed='unexecuted').first()
    
    if match:
        start_time = datetime.now().replace(microsecond=0)
        match.host_name = host_name
        match.start_time = start_time
        match.processed = 'in progress'
        db.session.commit()
        
        updated_match = Match.query.filter_by(match_id=match.match_id).first()

        log_file_name_value = log_file_name(updated_match.group_id, updated_match.match_index, host_name, updated_match.left_team, updated_match.right_team)

        updated_match.log_file_name = log_file_name_value
        db.session.commit()
        
        return jsonify({
            "match_id": updated_match.match_id,
            "group_id": updated_match.group_id,
            "match_index": updated_match.match_index,
            "host_name": updated_match.host_name,
            "start_time": updated_match.start_time,
            "left_team": updated_match.left_team,
            "right_team": updated_match.right_team,
            "log_file_name": updated_match.log_file_name,
        })
    else:
        return jsonify()

@bp.route("/result", methods=["POST"])
@csrf.exempt
@require_api_key
def result():
    data = request.form.to_dict()
    host_name = data.get("host_name")
    start_time_str = data.get("start_time")
    match_id = data.get("match_id")
    left_team = data.get("left_team")
    right_team = data.get("right_team")
    left_score = data.get("left_score")
    right_score = data.get("right_score")
    processed = data.get("processed")
    log_file = data.get("log_file")

    start_time = datetime.strptime(start_time_str, '%a, %d %b %Y %H:%M:%S %Z')
    match = Match.query.filter_by(match_id=match_id,start_time=start_time).first()
    end_time = datetime.now().replace(microsecond=0)

    
    if match:
        group = Group.query.filter_by(group_id=match.group_id).first()
        log_directory_name = group.group_name
        executed_count = group.executed_count + 1
        host_name = match.host_name
        match_index = match.match_index
        match_index = str(match_index).zfill(5)

        # ログディレクトリを作成
        logs_dir = os.path.join('rcgame_flask', 'static', 'logs')
        log_dir_path = os.path.join(logs_dir, log_directory_name)
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)

        saved_files = []

        for file in request.files.getlist('log_file'):
            if file and file.filename:
                original_filename = file.filename
                save_path = os.path.join(log_dir_path, original_filename)
                file.save(save_path)
                saved_files.append(original_filename)
        
        # レコードを更新
        match.end_time = end_time
        match.left_team = left_team
        match.right_team = right_team
        match.left_score = left_score
        match.right_score = right_score
        match.processed = 'completed'
        match.log_directory_name = log_directory_name
        match.log_file = log_file
        db.session.commit()
        
        group.executed_count = executed_count
        db.session.commit()
        return jsonify({"message": "Match updated successfully"})
    else:
        return jsonify({"message": "Match not updated "})


    