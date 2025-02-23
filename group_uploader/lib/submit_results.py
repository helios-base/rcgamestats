import os
import glob
import requests
from urllib.parse import urljoin
from .config import config


def submit_results(group_data, results):
    """
    Submit results for each group file
    Args:
        group_data: group data in JSON format
        results: list of results (filename, left_score, right_score)
    """
    try:
        group_id = group_data["group_id"]
    except KeyError:
        print("Group data does not contain group_id")
        return False

    if not results or len(results) == 0:
        return False

    for r in results:
        print(f"==== Submitting result for {r[0]} ====")
        __submit_result(group_id, r)

    return True


def __get_submit_results_url():
    endpoint = "api/admin/submit_result"
    url = urljoin(config.SERVER_URL, endpoint)
    return url


def __submit_result(group_id, result):
    """
    Submit a result for the given filename
    Args:
        group_data: group data in JSON format
        result: tuple of (filename, left_score, right_score)
    """
    filename = result[0];
    left_score = result[1];
    right_score = result[2];
    if filename is None or left_score is None or right_score is None:
        return False

    url = __get_submit_results_url()

    headers = {
        "Accept": "application/json",
        "x-api-key": config.API_KEY
    }

    data = {
        "type": "submit_result",
        "group_id": group_id,
        "host_name" : config.HOST_NAME,
        "left_team_name": config.LEFT_TEAM_NAME,
        "right_team_name": config.RIGHT_TEAM_NAME,
        "left_team_version": config.LEFT_TEAM_VERSION,
        "right_team_version": config.RIGHT_TEAM_VERSION,
        "left_score": left_score,
        "right_score": right_score,
        "log_file_name": filename,
    }

    filepaths = glob.glob(os.path.join(config.GROUP_DIR, f"{filename}*"))
    files = [('log_file', (open(f, 'rb'))) for f in filepaths]

    print(f"Submitting result at {url}")
    print(f"Result data: {data}")

    try:
        response = requests.post(url, headers=headers, data=data, files=files)
        response.raise_for_status()
        print(f"Response content: {response.text}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e}")
        print(f"Response content: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"RequestException: {e}")
        print(f"Response content: {response.text}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Response content: {response.text}")
        return False
