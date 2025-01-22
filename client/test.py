import requests

def create_user(username):
    url = "http://127.0.0.1:5000/communication/create_user/{}".format(username)
    response = requests.post(url)
    if response.status_code == 200:
        data = response.json()
        print("User created successfully!")
        print("host_name:", data['host_name'])
        print("API Key:", data['api_key'])
    else:
        print("Failed to create user. Status code:", response.status_code)
        print("Response:", response.text)

if __name__ == "__main__":
    username = input("Enter a username: ")
    create_user(username)