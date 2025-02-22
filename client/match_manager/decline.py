import os
import requests
from datetime import datetime
from config import config

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

    print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}] Decline match response content: {response.text}")

