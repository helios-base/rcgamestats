import requests
import json
import random
import string

def result_post_request(response_data):
    response_data["left_score"] = random.randint(1, 4)
    response_data["right_score"] = random.randint(1, 4)

    log_file = f"{response_data['match_index']}_logfile"

    # 変更したデータをサーバに返す
    result_post_url = "http://127.0.0.1:5000/communication/result"
    result_response = requests.post(result_post_url, json={
        "match_id": response_data["match_id"],
        "left_team": response_data["left_team"],
        "right_team": response_data["right_team"],
        "left_score": response_data["left_score"],
        "right_score": response_data["right_score"],
        "processed": response_data["processed"],
        "log_file": log_file
    })

    # サーバからのレスポンスを表示
    print("サーバに返したデータ:","left_score:", response_data["left_score"],"right_score:",response_data["right_score"])

    return result_response.json()