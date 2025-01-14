import json
import os
from flask import jsonify, request
from rcgame_flask.communication import bp
from rcgame_flask.db import get_db
from datetime import datetime


@bp.route("/callback",methods=["POST"]) 
def callback():
    print(request.data.decode())
    return jsonify({"kekka": "受け取ったよ!"})


@bp.route("/api", methods=["POST"]) 
def api():
    data = request.get_json()
    host_name = data.get("host_name")
    
    db = get_db()
    
    # `processed` カラムが `unexecuted` の1レコードを取得
    match = db.execute("SELECT * FROM matches WHERE processed = 'unexecuted' LIMIT 1").fetchone()
    
    if match:
        # 現在の日時を取得
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # レコードを更新
        db.execute(
            "UPDATE matches SET host_name = ?, start_time = ?, processed = ? WHERE match_id = ?",
            (host_name, start_time, 'in progress', match['match_id'])
        )
        db.commit()
        # 更新したレコードを再取得
        updated_match = db.execute("SELECT * FROM matches WHERE match_id = ?", (match['match_id'],)).fetchone()
        
        # 更新したレコードをJSON形式で返す
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
    else :
        return jsonify()


@bp.route("/result", methods=["POST"])
def result():
    data = request.get_json()
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
        group = db.execute("SELECT group_name FROM group_matches WHERE group_id = ?", (match['group_id'],)).fetchone()
        log_directory_name = group['group_name']
        executed_count = group['executed_count'] + 1
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

        # ディレクトリとファイルを作成
        logs_dir = os.path.join('rcgame_flask', 'static', 'logs')
        log_dir_path = os.path.join(logs_dir, log_directory_name)
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)

        # ファイルを作成
        matches = db.execute("SELECT * FROM matches WHERE group_id = ? AND log_directory_name = ?", (match['group_id'], log_directory_name)).fetchall()
        for match in matches:
            # ファイルを作成
            log_file_path = os.path.join(log_dir_path, log_file)
            with open(log_file_path, 'w') as f:
                f.write(f"Match ID: {match_id}\n")
                f.write(f"Group ID: {match['group_id']}\n")
                f.write(f"Left Team: {left_team}\n")
                f.write(f"Right Team: {right_team}\n")
                f.write(f"Left Score: {left_score}\n")
                f.write(f"Right Score: {right_score}\n")
                f.write(f"Processed: {processed}\n")
                f.write(f"End Time: {end_time}\n")

        return jsonify({"message": "レコードが更新され、ログファイルが作成されました"})
    
    