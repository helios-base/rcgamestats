import requests
from urllib.parse import urljoin
from .config import config


def get_create_group_endpoint():
    create_group_endpoint = "group/admin/create_group"
    create_group_url = urljoin(config.SERVER_URL, create_group_endpoint)
    return create_group_url


def create_group(results):
    """
    Create a group with the given filenames
    Args:
        filenames: list of filenames (no extension)
    """
    if not results or len(results) == 0:
        print(f"No group files found in {config.GROUP_DIR}")
        return None

    url = get_create_group_endpoint()
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

    response = requests.post(url, headers=headers, json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e}")
        print(f"Response content: {response.text}")
        return None

    print(f"Response content: {response.text}")
    data = response.json()
    return data
