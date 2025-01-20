import os
from flask import jsonify, request
from rcgame_flask.communication import bp
from rcgame_flask.models import db, certificate_key, matches, group_matches
from datetime import datetime
from functools import wraps
from flask import url_for

def certification_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        data = request.get_json()
        host_name = data.get("host_name")

        certificate = certificate_key.query.filter_by(host_name=host_name, permit_flag='true').first()
    
        # デバッグ情報を追加
        print("Received host_name:", host_name)
        print("Certificate found:", certificate)

        if certificate is None:
            return jsonify({"error": "認証が必要です"}), 403

        return view(**kwargs)
    
    return wrapped_view

@bp.route("/callback", methods=["POST"])
def callback():
    print(request.data.decode())
    return jsonify({"kekka": "受け取ったよ!"})

@bp.route("/certification", methods=["POST"])
def certification():
    data = request.get_json()
    api_key = data.get("api_key")
    host_name = data.get("host_name")

    new_certificate = certificate_key(host_name=host_name, api_key=api_key)
    db.session.add(new_certificate)
    db.session.commit()
    
    certificate = certificate_key.query.filter_by(api_key=api_key, host_name=host_name).first()
    if certificate:
        return jsonify({"message": "認証が成功しました"}), 200
    else:
        return jsonify({"error": "認証に失敗しました"}), 403

@bp.route("/api", methods=["POST"])
def api():
    data = request.get_json()
    host_name = data.get("host_name")

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
            "end_time": updated_match.end_time,
            "left_team": updated_match.left_team,
            "right_team": updated_match.right_team,
            "left_score": updated_match.left_score,
            "right_score": updated_match.right_score,
            "processed": updated_match.processed,
            "log_directory_name": updated_match.log_directory_name,
            "log_file": updated_match.log_file
        })
    else:
        return jsonify()

@bp.route("/result", methods=["POST"])
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
        for file in request.files.getlist('files'):
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
    