from flask import jsonify, request
from rcgame_flask.communication import bp
from rcgame_flask.db import get_db
from datetime import datetime
import json

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
        start_time = datetime.now()
        
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
            "host_name": updated_match["host_name"],
            "start_time": updated_match["start_time"],
            "end_time": updated_match["end_time"],
            "left_team": updated_match["left_team"],
            "right_team": updated_match["right_team"],
            "left_score": updated_match["left_score"],
            "right_score": updated_match["right_score"],
            "processed": updated_match["processed"]
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

    db = get_db()

    match = db.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
    end_time = datetime.now()
    if match:
        # レコードを更新
        db.execute(
            "UPDATE matches SET end_time = ?, left_team = ?, right_team = ?, left_score = ?, right_score = ?, processed = ? WHERE match_id = ?",
            (end_time, left_team, right_team, left_score, right_score, 'completed', match_id)
        )
        db.commit()

        return jsonify({"message": "レコードが更新されました"})