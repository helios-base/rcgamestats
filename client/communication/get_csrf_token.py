import requests
from config import Config


def get_csrf_token():
    url = f"http://{Config.SERVER_URL}/auth/get_csrf_token"
    response = requests.get(url)
    return response.json()['csrf_token']
