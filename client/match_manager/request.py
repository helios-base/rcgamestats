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

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None

    json_message = response.json()
    if "message" in json_message:
        logger.info(f"request_match: (message) {json_message['message']}")
        return None
    if "error" in json_message:
        logger.error(f"request_match: (error) {json_message['error']}")
        return None

    match = Match.from_json(json_message)
    return match
