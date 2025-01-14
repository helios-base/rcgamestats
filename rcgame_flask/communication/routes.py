import os
from flask import jsonify, request
from rcgame_flask.communication import bp
from rcgame_flask.db import get_db
from datetime import datetime

@bp.route("/callback", methods=["POST"])
def callback():
    print(request.data.decode())
    return jsonify({"kekka": "受け取ったよ!"})

@bp.route("/api", methods=["POST"])
def api():
    data = request.get_json()
    host_name = data.get("host_name")
    
    db = get_db()
    
    match = db.execute("SELECT * FROM matches WHERE processed = 'unexecuted' LIMIT 1").fetchone()
    
    if match:
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        db.execute(
            "UPDATE matches SET host_name = ?, start_time = ?, processed = ? WHERE match_id = ?",
            (host_name, start_time, 'in progress', match['match_id'])
        )
        db.commit()
        updated_match = db.execute("SELECT * FROM matches WHERE match_id = ?", (match['match_id'],)).fetchone()
        
        return jsonify({
            "match_id": updated_match["match_id"],
            "group_id": updated_match["group_id"],
            "match_index": updated_match["match_index"],
            "host_name": updated_match["host_name"],
            "start_time": updated_match["start_time"],
            "end_time": updated_match["end_time"],
            "left_team": updated_match["left_team"],
            "right_team": updated_match["right_team"],
            "left_score": updated_match["left_score"],
            "right_score": updated_match["right_score"],
            "processed": updated_match["processed"],
            "log_directory_name": updated_match["log_directory_name"],
            "log_file": updated_match["log_file"]
        })
    else:
        return jsonify()

@bp.route("/result", methods=["POST"])
def result():
    # ファイルを受け取る
    if 'log_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    files = request.files.getlist('log_file')
    if not files:
        return jsonify({"error": "No selected files"}), 400
        
    data = request.form.to_dict()
    match_id = data.get("match_id")
    left_team = data.get("left_team")
    right_team = data.get("right_team")
    left_score = data.get("left_score")
    right_score = data.get("right_score")
    processed = data.get("processed")
    log_file = data.get("log_file")
    db = get_db()

    match = db.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if match:
        group = db.execute("SELECT group_name, executed_count FROM group_matches WHERE group_id = ?", (match['group_id'],)).fetchone()
        log_directory_name = group['group_name']
        executed_count = group['executed_count'] + 1

        # ログディレクトリを作成
        logs_dir = os.path.join('rcgame_flask', 'static', 'logs')
        log_dir_path = os.path.join(logs_dir, log_directory_name)
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)

        log_file_dir_path = os.path.join(log_dir_path, log_file)
        if not os.path.exists(log_file_dir_path):
            os.makedirs(log_file_dir_path)
            
        saved_files = []
        for file in files:
            if file:
                filename = file.filename
                save_path = os.path.join(log_file_dir_path, filename)
                file.save(save_path)
                saved_files.append(filename)
        
        # レコードを更新
        db.execute(
            "UPDATE matches SET end_time = ?, left_team = ?, right_team = ?, left_score = ?, right_score = ?, processed = ?, log_directory_name = ?, log_file = ? WHERE match_id = ?",
            (end_time, left_team, right_team, left_score, right_score, 'completed', log_directory_name, log_file, match_id)
        )
        
        db.execute(
            "UPDATE group_matches SET executed_count = ? WHERE group_id = ?",
            (executed_count, match['group_id'])
        )

        db.commit()

        return jsonify({"message": "レコードが更新され、ログファイルが保存されました"})
    else:
        return jsonify({"message": "マッチが見つかりませんでした"})