import requests
import logging
import json
from datetime import datetime
from config import config

logger = logging.getLogger("client")


def decline_match(match):
    """
    Decline the match.
    """
    url = f"http://{config.SERVER_URL}/group/decline_assignment"

    headers = {
        "Accept": "application/json",
        'x-api-key': config.API_KEY
    }

    data = {
        "type": "decline_match",
        "host_name": config.HOST_NAME,
        "match_id": match.match_id,
        "token": match.token,
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()

    # compact_text = json.dumps(response.json(), separators=(",", ":"))
    # logger.info(f"Decline match response content: {compact_text}")
    logger.info(f"Decline match response content: {response.json()}")
