import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from config import config
from host_manager import load_token

logger = logging.getLogger("client")


def decline_match(match):
    """
    Decline the match.
    """
    endpoint = "api/decline_match"
    url = urljoin(config.SERVER_URL + '/', endpoint)

    host_id, host_token = load_token()
    if host_token is None:
        logger.error("decline_match: Host token does not exist.")
        return

    headers = {
        "Accept": "application/json",
        'x-api-key': config.API_KEY
    }

    data = {
        "type": "decline_match",
        "host_id": host_id,
        "host_name": config.HOST_NAME,
        "host_token": host_token,
        "match_id": match.match_id,
        "match_token": match.match_token,
    }

    with requests.Session() as session:
        retry_count = 3
        retries = Retry(total=retry_count, backoff_factor=0.3, status_forcelist=[502, 503, 504], allowed_methods=["POST"])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))

        try:
            response = session.post(url, headers=headers, json=data, timeout=(3, 10))
            response.raise_for_status()
            logger.info(f"Decline match response content: {response.json()}")
            return
        except requests.exceptions.HTTPError as e:
            try:
                response_data = response.json()
                error_msg = response_data.get("error", "")
            except Exception:
                error_msg = ""
            logger.error(f"decline_match: HTTP error occurred: [{error_msg}] {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"decline_match: Request error occurred: {e}")
        except Exception as e:
            logger.error(f"decline_match: An error occurred: {e}")
        finally:
            logger.info(f"decline_match: Failed after {retry_count} retries.")

    # max_retries = 3
    # retry_delay = 5  # seconds
    # for i in range(max_retries):
    #     try:
    #         response = requests.post(url, headers=headers, data=data)
    #         response.raise_for_status()
    #         # compact_text = json.dumps(response.json(), separators=(",", ":"))
    #         # logger.info(f"Decline match response content: {compact_text}")
    #         logger.info(f"Decline match response content: {response.json()}")
    #         return
    #     except requests.exceptions.HTTPError as e:
    #         logger.error(f"decline_match: HTTP error occurred: {e}")
    #     except requests.exceptions.RequestException as e:
    #         logger.error(f"decline_match: Request error occurred: {e}")
    #     except Exception as e:
    #         logger.error(f"decline_match: An error occurred: {e}")

    #     logger.info(f"decline_match: Retry {i+1}/{max_retries} after {retry_delay} seconds.")
    #     time.sleep(retry_delay)

    # logger.error(f"decline_match: Failed after {max_retries} retries.")
