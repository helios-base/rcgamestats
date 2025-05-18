import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from .config import config


def submit_group(results):
    """
    Create a group with the given filenames
    Args:
        filenames: list of filenames (no extension)
    """
    if not results or len(results) == 0:
        print(f"No group files found in {config.GROUP_DIR}")
        return None

    endpoint = "api/admin/submit_group"
    url = urljoin(config.SERVER_URL + '/', endpoint)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": config.API_KEY
    }
    data = {
        "group_name": config.GROUP_NAME,
        "left_team_name": config.LEFT_TEAM_NAME,
        "left_team_version": config.LEFT_TEAM_VERSION,
        "right_team_name": config.RIGHT_TEAM_NAME,
        "right_team_version": config.RIGHT_TEAM_VERSION,
        "number_of_matches": len(results),
        "description": config.DESCRIPTION,
    }

    print(f"Creating group at {url}")
    print(f"Group data: {data}")

    with requests.Session() as session:
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504], allowed_methods=["POST"])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))
        try:
            # response = requests.post(url, headers=headers, json=data)
            response = session.post(url, headers=headers, json=data)
            response.raise_for_status()
            print(f"Response content: {response.text}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTPError: {e}")
            print(f"Response content: {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"RequestException: {e}")
            print(f"Response content: {response.text}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            print(f"Response content: {response.text}")
            return None

    return None
