import requests
from config import Config
def create_user(username):
    
    url = f"http://{Config.SERVER_URL}/communication/create_user/{username}"
    response = requests.post(url)

    if response.status_code == 200:
        data = response.json()
        print("User created successfully!")
        print("host_name:", data['host_name'])
        print("API Key:", data['api_key'])
        return data['host_name'], data['api_key']
    else:
        print("Failed to create user. Status code:", response.status_code)
        print("Response:", response.text)
        return None, None  
    