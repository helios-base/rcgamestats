import sys
import csv
import requests
from getpass import getpass


# sample of csv file

# team_name,version,synch_mode,description,archive_file
# TeamA,1.0,True,Description of TeamA,/path/to/fileA.tar.gz
# TeamB,1.1,False,Description of TeamB,/path/to/fileB.tar.gz

#  server URL
BASE_URL = "http://localhost:5000"
TEAM_CSV_FILE = "teams.csv"

# read login credentials
username = input("Username: ")
password = getpass("Password: ")

# login URL and data
login_url = f"{BASE_URL}/auth/login"
login_data = {
    "username": username,
    "password": password
}

# start a session
session = requests.Session()

# send a POST request to login
response = session.post(login_url, data=login_data)

if response.status_code != 200:
    print(f"Failed to log in: {response.status_code}")
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
            description = row['description']
            archive_file_path = row['archive_file']

            upload_url = f"{BASE_URL}/team/upload"
            form_data = {
                "team_name": team_name,
                "version": version,
                "synch_mode": synch_mode,
                "description": description
            }

            with open(archive_file_path, 'rb') as file:
                files = {'archive_file': file}
                response = session.post(upload_url, data=form_data, files=files)
                if response.status_code == 200:
                    print(f"Successfully uploaded team: {team_name}")
                else:
                    print(f"Failed to upload team: {team_name}, Status Code: {response.status_code}")
        except FileNotFoundError:
            print(f"File not found: {archive_file_path}")
            sys.exit(1)
        except KeyError:
            print(f"Invalid CSV format: {archive_file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Failed to upload team: {team_name}, Error: {e}")
            sys.exit(1)

print("All teams uploaded successfully")
sys.exit(0)
