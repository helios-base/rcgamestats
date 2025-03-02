import os
import glob
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from config import config
from host_manager import load_token

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
    endpoint = "api/submit_result"
    url = urljoin(config.SERVER_URL + '/', endpoint)

    host_id, host_token = load_token()
    if host_token is None:
        logger.error("submit_result: Host token does not exist.")
        return None

    if match.host_id != host_id:
        logger.error(f"submit_result: Host ID does not match. match({match.host_id}) != own({host_id})")
        return None

    headers = {
        "Accept": "application/json",
        'x-api-key': config.API_KEY
    }

    match_data = {
        "type": "submit_result",
        "host_id": match.host_id,
        "host_name": config.HOST_NAME,
        "host_token": host_token,
        "match_id": match.match_id,
        "match_token": match.match_token,
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

    with requests.Session() as session:
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[502, 503, 504], allowed_methods=["POST"])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))

        try:
            response = session.post(url, headers=headers, data=match_data, files=files, timeout=(3, 10))
            response.raise_for_status()
            logger.info(f"SubmitResponse: {response.json()}")
        except requests.exceptions.HTTPError as e:
            try:
                response_data = response.json()
                error_msg = response_data.get("error", "")
            except Exception:
                error_msg = ""
            # If the error is not 5xx, it is not a server error.
            if response.status_code == 401:
                logger.error(f"submit_result: The match token may be changed. [{error_msg}] {e}")
            elif response.status_code == 404:
                logger.error(f"submit_result: The match may be deleted. [{error_msg}] {e}")
            elif response.status_code == 409:
                logger.error(f"submit_result: Some information may be wrong. [{error_msg}] {e}")
            elif response.status_code == 410:
                logger.error(f"submit_result: The match may be reset. [{error_msg}] {e}")
            else:
                logger.error(f"submit_result: Client error occurred: [{error_msg}] {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"submit_result: Request error occurred: {e}")
        except Exception as e:
            logger.error(f"submit_result: An error occurred: {e}")
        finally:
            for f in files:
                f[1].close()

    __move_log_files(file_paths, os.path.join(config.LOG_DIR, match.group_name))

    # max_retries = 3
    # retry_delay = 5  # seconds

    # for i in range(max_retries):
    #     try:
    #         response = requests.post(url, headers=headers, data=match_data, files=files)
    #         response.raise_for_status()
    #         logger.info(f"SubmitResponse: {response.json()}")
    #         break
    #     except requests.exceptions.HTTPError as e:
    #         if 400 <= response.status_code < 500:
    #             response_data = response.json()
    #             error_msg = ""
    #             if "error" in response_data:
    #                 error_msg = response_data["error"]
    #             if response.status_code == 401:
    #                 logger.error(f"submit_result: The match token may be changed. [{error_msg}] {e}")
    #             elif response.status_code == 404:
    #                 logger.error(f"submit_result: The match may be deleted. [{error_msg}] {e}")
    #             elif response.status_code == 409:
    #                 logger.error(f"submit_result: Some information may be wrong. [{error_msg}] {e}")
    #             elif response.status_code == 410:
    #                 logger.error(f"submit_result: The match may be reset. [{error_msg}] {e}")
    #             else:
    #                 logger.error(f"submit_result: Client error occurred: [{error_msg}] {e}")
    #             break  # No need to retry
    #         logger.error(f"submit_result: HTTP error occurred: {e}")
    #     except requests.exceptions.RequestException as e:
    #         logger.error(f"submit_result: Request error occurred: {e}")
    #     except Exception as e:
    #         logger.error(f"submit_result: An error occurred: {e}")

    #     logger.info(f"submit_result: Retry {i+1}/{max_retries} after {retry_delay} seconds.")
    #     time.sleep(retry_delay)

    # __move_log_files(file_paths, os.path.join(config.LOG_DIR, match.group_name))
