import sys
import requests
import argparse
from urllib.parse import urljoin
from read_group import get_log_filenames

parser = argparse.ArgumentParser(description="Group uploader")
parser.add_argument("--server-url", required=True, help="The URL of the server", default="http://127.0.0.1:5000")
parser.add_argument("--api-key", required=True, help="The API key")
parser.add_argument("--group-dir", required=True, help="The directory containing the group files")
parser.add_argument("--left-team-name", required=True, help="The name of the team on the left")
parser.add_argument("--left-team-version", required=True, help="The version of the team on the left")
parser.add_argument("--right-team-name", required=True, help="The name of the team on the right")
parser.add_argument("--right-team-version", required=True, help="The version of the team on the right")
parser.add_argument("--description", help="The description of the group")
args = parser.parse_args()


def get_login_endpoint():
    base_url = args.server_url
    login_endpoint = "auth/login"
    login_url = urljoin(base_url, login_endpoint)
    return login_url


def get_create_group_endpoint():
    base_url = args.server_url
    create_group_endpoint = "group/api/create_group"
    create_group_url = urljoin(base_url, create_group_endpoint)
    return create_group_url


def create_group():
    filenames = get_log_filenames(args.group_dir)
    if not filenames or len(filenames) == 0:
        print(f"No group files found in {args.group_dir}")
        return False

    url = get_create_group_endpoint()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": args.api_key
    }
    data = {
        "left_team_name": args.left_team_name,
        "left_team_version": args.left_team_version,
        "right_team_name": args.right_team_name,
        "right_team_version": args.right_team_version,
        "number_of_matches": len(filenames),
        "description": "",
    }

    print(f"Creating group at {url}")
    print(f"Group data: {data}")

    response = requests.post(url, headers=headers, json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e}")
        print(f"Response content: {response.text}")
        return False

    print(f"Response content: {response.text}")
    return True


if __name__ == "__main__":
    create_group()