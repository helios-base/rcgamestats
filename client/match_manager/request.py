import requests
import logging
import json
# from datetime import datetime
from config import config
from .match import Match

logger = logging.getLogger("client")


def request_match():
    """
    Request a match from the server.
    """
    url = f"http://{config.SERVER_URL}/group/request_match"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        'x-api-key': config.API_KEY
    }
    data = {
        "type": "request_match",
        "host_name": config.HOST_NAME
    }

    response = requests.post(url, headers=headers, json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return None

    # レスポンスに含まれるjsonデータに "message" が含まれている場合はエラーとして処理する
    if "message" in response.json():
        logger.info(f"RequestResponse {response.json()['message']}")
        return None

    # response_text = response.txt.replace("\n", "")
    # logger.info(f"Response content: {response_text}")
    # compact_text = json.dumps(response.json(), separators=(",", ":"))
    # logger.info(f"Response content: {compact_text}")

    # logger.info(f"RequestResponse {response.json()}")

    match = Match.from_json(response.json())
    return match
