import os
import time
import requests
import glob
import logging
from urllib.parse import urljoin
from config import config

logger = logging.getLogger("client")


def __move_log_files(file_paths, log_dir):
    """
    Move log files from temporal directory to log directory.
    """
    # logger.info(f"Move logs to {log_dir}")
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
    endpoint = "group/submit_result"
    url = urljoin(config.SERVER_URL, endpoint)

    headers = {
        "Accept": "application/json",
        'x-api-key': config.API_KEY
    }

    match_data = {
        "type": "submit_result",
        "host_id": match.host_id,
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
    # files = [('log_file', (os.path.basename(file_path), open(file_path, 'rb'))) for file_path in file_paths]
    files = [('log_file', (open(file_path, 'rb'))) for file_path in file_paths]
    # files = [(os.path.basename(file_path), open(file_path, 'rb')) for file_path in file_paths]

    # logger.info(f"Submit result: {match_data}")
    logger.info(f"Submitting result {match.group_name}/{match.index}, {match.left_score} - {match.right_score}")

    max_retries = 3
    retry_delay = 5  # seconds

    for i in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=match_data, files=files)
            response.raise_for_status()
            logger.error(f"SubmitResponse: {response.json()}")
            break
        except requests.exceptions.HTTPError as e:
            logger.error(f"submit_result: HTTP error occurred: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"submit_result: Request error occurred: {e}")
        except Exception as e:
            logger.error(f"submit_result: An error occurred: {e}")

        logger.info(f"submit_result: Retry {i+1}/{max_retries} after {retry_delay} seconds.")
        time.sleep(retry_delay)

    __move_log_files(file_paths, os.path.join(config.LOG_DIR, match.group_name))
