import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from config import config
from .token import load_token, save_token

logger = logging.getLogger("client")


def register_host():
    host_id, host_token = load_token()

    endpoint = "api/register_host"
    url = urljoin(config.SERVER_URL + '/', endpoint)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        'x-api-key': config.API_KEY
    }
    data = {
        "host_id": host_id,
        "host_name": config.HOST_NAME,
        "host_token": host_token
    }

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[502, 503, 504], allowed_methods=["POST"])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    try:
        response = session.post(url, headers=headers, json=data, timeout=(3, 10))
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False

    if response.status_code != 200:
        logger.error(f"Failed to register host. {response.status_code} {response.text}")
        return False

    json_message = response.json()
    if "message" in json_message:
        if "host_id" in json_message:
            logger.info(f"Received host_id: {json_message.get('host_id')}")
            host_id = json_message.get("host_id")

        if "host_token" in json_message:
            logger.info(f"Received host_token: {json_message.get('host_token')}")
            host_token = json_message.get("host_token")
            return save_token(host_id, host_token)
        else:
            logger.info(f"message: {json_message['message']}")
            return True
    if "error" in json_message:
        logger.error(f"Failed to register host. {json_message['error']}")
        return False
    return False
