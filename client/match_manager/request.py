import requests
from datetime import datetime
from config import config
from .match import Match


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
    response.raise_for_status()

    print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}]((request_post) Response content:", response.text)
    match = Match.from_json(response.json())
    
    return match
