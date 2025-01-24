import os
from flask import jsonify, request
from rcgame_flask.communication import bp
from rcgame_flask.models import db, certificate_key, matches, group_matches
from datetime import datetime
from functools import wraps

import secrets

def generate_api_key():
   return secrets.token_hex(16)

def require_api_key(f):
   @wraps(f)
   def decorated_function(*args, **kwargs):
       api_key = request.headers.get('x-api-key')
       host_name = request.headers.get('x-host-name')
       user = certificate_key.query.filter_by(api_key=api_key, host_name=host_name).first()
       if user is None:
           return jsonify({"error": "認証に失敗しました。無効なAPIキーです。"}), 401
       return f(*args, **kwargs)
   return decorated_function

@bp.route("/create_user/<host_name>", methods=["POST"])
def create_user(host_name):
    existing_user = certificate_key.query.filter_by(host_name=host_name).first()
    if existing_user:
        return {'error': 'host_name already exists'}, 400

    api_key = generate_api_key()
    new_user = certificate_key(host_name=host_name, api_key=api_key)
    db.session.add(new_user)
    db.session.commit()
    return {'host_name': host_name, 'api_key': api_key}

@bp.route("/callback", methods=["POST"])
@require_api_key
def callback():
    print(request.data.decode())
    return jsonify({"kekka": "受け取ったよ!"})

@bp.route("/api", methods=["POST"])
@require_api_key
def api():

    data = request.get_json()
    host_name = data.get("host_name")
    api_key = data.get("api_key")

    if not host_name or not api_key:
        return jsonify({"error": "Host-NameまたはAPI-Keyが不足しています"}), 400
    
    cert_key = certificate_key.query.filter_by(host_name=host_name, api_key=api_key).first()
    stpo_check_response = cert_key.stop_check
    if cert_key.stop_check is True:
        return jsonify({"stop_check": stpo_check_response})

    match = matches.query.filter_by(processed='unexecuted').first()
    
    if match:
        start_time = datetime.now()
        
        match.host_name = host_name
        match.start_time = start_time
        match.processed = 'in progress'
        db.session.commit()
        
        updated_match = matches.query.filter_by(match_id=match.match_id).first()


        
        return jsonify({
            "match_id": updated_match.match_id,
            "group_id": updated_match.group_id,
            "match_index": updated_match.match_index,
            "host_name": updated_match.host_name,
            "start_time": updated_match.start_time,
            "left_team": updated_match.left_team,
            "right_team": updated_match.right_team,
        })
    else:
        return jsonify()

@bp.route("/result", methods=["POST"])
@require_api_key
def result():
    data = request.form.to_dict()
    host_name = data.get("host_name")
    match_id = data.get("match_id")
    left_team = data.get("left_team")
    right_team = data.get("right_team")
    left_score = data.get("left_score")
    right_score = data.get("right_score")
    processed = data.get("processed")
    log_file = data.get("log_file")

    match = matches.query.filter_by(match_id=match_id).first()
    end_time = datetime.now()
    if match:
        group = group_matches.query.filter_by(group_id=match.group_id).first()
        log_directory_name = group.group_name
        executed_count = group.executed_count + 1

        # ログディレクトリを作成
        logs_dir = os.path.join('rcgame_flask', 'static', 'logs')
        log_dir_path = os.path.join(logs_dir, log_directory_name)
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)

        log_file_dir_path = os.path.join(log_dir_path, log_file)
        if not os.path.exists(log_file_dir_path):
            os.makedirs(log_file_dir_path)
            
        saved_files = []

        for file in request.files.getlist('log_file'):
            if file:
                filename = file.filename
                save_path = os.path.join(log_file_dir_path, filename)
                file.save(save_path)
                saved_files.append(filename)
        
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


    