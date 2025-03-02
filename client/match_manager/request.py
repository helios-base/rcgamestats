import logging
# from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from config import config
from .match import Match
from host_manager import load_token

logger = logging.getLogger("client")


def request_match():
    """
    Request a match from the server.
    """
    endpoint = "api/request_match"
    url = urljoin(config.SERVER_URL + '/', endpoint)

    host_id, host_token = load_token()
    if host_token is None:
        logger.error("request_match: Host token does not exist.")
        return None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        'x-api-key': config.API_KEY
    }
    data = {
        "type": "request_match",
        "host_id": host_id,
        "host_name": config.HOST_NAME,
        "host_token": host_token
    }

    with requests.Session() as session:
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[502, 503, 504], allowed_methods=["POST"])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))

        try:
            response = session.post(url, headers=headers, json=data, timeout=(3, 10))
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                response_data = response.json()
                error_msg = response_data.get("error", "")
            except Exception:
                error_msg = ""
            if response.status_code == 404:
                logger.error(f"request_match: [{error_msg}] {e}")
                return None
            logger.error(f"HTTP error occurred: [{response.status_code}] {error_msg} {e}")
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
