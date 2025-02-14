import sys
import csv
import requests
from getpass import getpass
from bs4 import BeautifulSoup


# sample of csv file

# team_name,version,synch_mode,description,archive_file
# TeamA,1.0,True,Description of TeamA,/path/to/fileA.tar.gz
# TeamB,1.1,False,Description of TeamB,/path/to/fileB.tar.gz

#  server URL
BASE_URL = "http://localhost:5000"
TEAM_CSV_FILE = "teamlist.csv"


# start a session
session = requests.Session()

# get CSRF token from the login page
login_url = f"{BASE_URL}/auth/login"
response = session.get(login_url)
if response.status_code != 200:
    print(f"Failed to get CSRF token: {response.status_code}")
    sys.exit(1)
print(f"Successfully got something. Status Code: {response.status_code}")

soup = BeautifulSoup(response.text, "html.parser")
csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

# read login credentials
username = input("Username: ")
password = getpass("Password: ")

login_data = {
    "username": username,
    "password": password,
    "csrf_token": csrf_token
}

# send a POST request to login
response = session.post(login_url, data=login_data)

if response.status_code != 200:
    print(f"Failed to log in: {response.status_code}")
    print(f" response.status_code: {response.status_code}")
    print(f" response.text: {response.text}")
    print("Please check your credentials")
    sys.exit(1)

print("Logged in successfully")

# read teams from the csv file
with open(TEAM_CSV_FILE, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            team_name = row['team_name']
            version = row['version']
            synch_mode = row['synch_mode']
            archive_file_path = row['archive_path']
            description = row['description']

            upload_url = f"{BASE_URL}/team/upload"
            form_data = {
                "team_name": team_name,
                "version": version,
                "synch_mode": synch_mode,
                "description": description,
                "csrf_token": csrf_token
            }

            print(f"form_data: {form_data}")

            with open(archive_file_path, 'rb') as file:
                files = {'archive_file': file}
                response = session.post(upload_url, data=form_data, files=files)
                if response.status_code == 200:
                    print(f"Successfully uploaded team: {team_name} {version}")
                else:
                    print(f"Failed to upload team: {team_name} {version}, Status Code: {response.status_code}")
                    print(f" response.text: {response.text}")
        except FileNotFoundError:
            print(f"File not found: {archive_file_path}")
            sys.exit(1)
        except KeyError:
            print(f"Invalid CSV format: {archive_file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Failed to upload team: {team_name}, Error: {e}")
            sys.exit(1)

sys.exit(0)
