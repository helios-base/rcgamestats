import os
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from datetime import datetime
import argparse

parser = argparse.ArgumentParser(description="Team uploader")
parser.add_argument("-u", "--server-url", required=True, help="The URL of the server", default="http://127.0.0.1:5000")
parser.add_argument("-a", "--api-key", required=True, help="The API key")
parser.add_argument("-n", "--team-name", required=True, help="The name of the new team")
parser.add_argument("-v", "--version", required=False, help="The version of the team")
parser.add_argument("-s", "--synch-mode", required=True, help="Support synch_mode")
parser.add_argument("-f", "--archive-file", required=True, help="The archive file")
parser.add_argument("-d", "--description", help="The description of the team")
args = parser.parse_args()


end_point = "api/admin/upload_team"
url = urljoin(args.server_url + "/", end_point)

team_name = args.team_name
if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9+]*$", team_name):
    print("Team name must start with an alphanumeric and be alphanumeric and +")
    exit(1)

team_version = args.version if args.version else datetime.now().strftime("%Y%m%d-%H%M%S")
sync_mode = True
if args.synch_mode == "0" or args.synch_mode.lower() == "false":
    sync_mode = False

description = args.description if args.description else ""

files = {"team_archive": open(args.archive_file, "rb")}
if not files["team_archive"]:
    print(f"Failed to open file: {args.archive_file}")
    exit(1)

headers = {
    "Accept": "application/json",
    "x-api-key": args.api_key,
}

team_data = {
    "type": "upload_team",
    "team_name": team_name,
    "team_version": team_version,
    "synch_mode": sync_mode,
    "description": description,
}

print(f"Uploading team: {team_name} version: {team_version} synch_mode: {sync_mode} description: [{description}]")

with requests.Session() as session:
    retry_count = 3
    retries = Retry(total=retry_count, backoff_factor=0.3, status_forcelist=[502, 503, 504], allowed_methods=["POST"])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    try:
        response = session.post(url, headers=headers, data=team_data, files=files, timeout=(3, 10))
        response.raise_for_status()
        print(f"Upload team response content: {response.json()}")
    except requests.exceptions.HTTPError as e:
        print(f"Upload team: HTTP error occurred: {e}")
        exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Upload team: Request error occurred: {e}")
        exit(1)
    except Exception as e:
        print(f"Upload team: An error occurred: {e}")
        exit(1)
    finally:
        files["team_archive"].close()

exit(0)
