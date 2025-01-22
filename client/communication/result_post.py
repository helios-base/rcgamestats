import requests
import json
import random
import string

def result_post_request(response_data, file_paths,api_key):
    response_data["left_score"] = random.randint(1, 4)
    response_data["right_score"] = random.randint(1, 4)

    log_file = f"{str(response_data['match_index']).zfill(5)}_logfile"

    headers = {
        'x-api-key': api_key
    }

    # ファイルを準備
    files = [('log_file', (open(file_path, 'rb'))) for file_path in file_paths]

    # 変更したデータをサーバに返す
    result_post_url = "http://127.0.0.1:5000/communication/result"
    result_response = requests.post(result_post_url, files=files, headers=headers, data={
        "match_id": response_data["match_id"],
        "left_team": response_data["left_team"],
        "right_team": response_data["right_team"],
        "left_score": response_data["left_score"],
        "right_score": response_data["right_score"],
        "processed": response_data["processed"],
        "log_file": log_file
    })
    print("result_post_request response status:", result_response.status_code)
    print("result_post_request response text:", result_response.text)

    # サーバからのレスポンスを表示
    print("サーバに返したデータ:","left_score:", response_data["left_score"],"right_score:",response_data["right_score"])

    return result_response.json()