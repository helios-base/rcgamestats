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
    
    return jsonify({"message": "受け取ったよ!"})