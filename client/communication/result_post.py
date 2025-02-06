import requests
import random
import os
import shutil
import re
from config import Config
from communication.get_csrf_token import get_csrf_token


def result_post_request(response_data, file_paths, api_key, host_name):
    csrf_token = get_csrf_token()
    log_file = f"{str(response_data['match_index']).zfill(5)}"

    headers = {
        'x-api-key': api_key,
        'X-CSRFToken': csrf_token
    }

    log_file_name = response_data["log_file_name"]

    print(log_file_name)
    print(response_data["group_id"])
    copied_file_paths = []

    for file_path in file_paths:
        original_filename = re.match(r'(.+)\.(.+)\.(.+)', os.path.basename(file_path))
        if original_filename:
            name = original_filename.group(1)
            ext1 = original_filename.group(2)
            ext2 = original_filename.group(3)
            new_file_name = f"{log_file_name}.{ext1}.{ext2}"
            new_file_path = os.path.join(Config.TEMPORAL_DIR, new_file_name)
            shutil.copy(file_path, new_file_path)
            copied_file_paths.append(new_file_path)

    files = [('log_file', (open(file_path, 'rb'))) for file_path in copied_file_paths]

    # 変更したデータをサーバに返す
    result_post_url = f"http://{Config.SERVER_URL}/communication/result"
    result_response = requests.post(result_post_url, files=files, headers=headers, data={
        "match_id": response_data["match_id"],
        "start_time": response_data["start_time"],
        "left_team": response_data["left_team"],
        "right_team": response_data["right_team"],
        "left_score": response_data["left_score"],
        "right_score": response_data["right_score"],
        "log_file": log_file
    })
    print("result_post_request response status:", result_response.status_code)
    print("result_post_request response text:", result_response.text)
    print("start_time:", response_data["start_time"])

    # サーバからのレスポンスを表示
    print("サーバに返したデータ:","left_score:", response_data["left_score"],"right_score:",response_data["right_score"])


    return result_response.json()