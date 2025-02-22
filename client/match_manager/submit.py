import os
import requests
import glob
from datetime import datetime
from config import config


def __move_log_files(file_paths, log_dir):
    """
    Move log files from temporal directory to log directory.
    """
    print("Move log files to:", log_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    for file_path in file_paths:
        if os.path.exists(file_path):
            new_file_path = os.path.join(log_dir, os.path.basename(file_path))
            os.rename(file_path, new_file_path)


def submit_result(match):
    """
    Submit the result to the server.
    """
    url = f"http://{config.SERVER_URL}/group/submit_result"

    headers = {
        "Accept": "application/json",
        'x-api-key': config.API_KEY
    }

    match_data = {
        "type": "submit_result",
        "host_name": config.HOST_NAME,
        "match_id": match.match_id,
        "token": match.token,
        "left_team_name": match.left_team_name,
        "right_team_name": match.right_team_name,
        "left_score": match.left_score,
        "right_score": match.right_score,
    }

    tmp_dir = config.TEMPORAL_DIR
    file_paths = glob.glob(os.path.join(tmp_dir, f"{match.log_file_name}*"))
    # print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}] (submit_result) Result file_paths:", file_paths)
    #files = [('log_file', (os.path.basename(file_path), open(file_path, 'rb'))) for file_path in file_paths]
    files = [('log_file', (open(file_path, 'rb'))) for file_path in file_paths]
    #files = [(os.path.basename(file_path), open(file_path, 'rb')) for file_path in file_paths]

    print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}] (submit_result) ", match_data)
    # print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}] (submit_result) Result files:", files)
    response = requests.post(url, headers=headers, data=match_data, files=files)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}] (submit_result) HTTPError:", e)
        print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}] (submit_result) Response content:", response.text)
        return None

    print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}] (submit_result) Response content:", response.text)
    __move_log_files(file_paths, os.path.join(config.LOG_DIR, match.group_name))
    return response.json()
