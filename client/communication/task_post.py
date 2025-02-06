import requests
from config import Config
from communication.get_csrf_token import get_csrf_token

def task_post_request(host_name,api_key):
    csrf_token = get_csrf_token()
    post_url = f"http://{Config.SERVER_URL}/group/request_match"

    print(f"csrf_token:[{csrf_token}]")

    # POST したいデータ
    data = {
        "host_name": host_name,
        "api_key": api_key
    }
    headers = {
        'X-CSRFToken': csrf_token,
        'x-api-key': api_key
    }

    # POST 送信
    response = requests.post(
        post_url,
        headers=headers,
        json=data
    )
    print("レスポンス内容:", response.text)
    response_json = response.json()
    if response_json is not None:
        if response_json.get('stop_check') is True:
            stop_file_path = Config.STOP_FILE_PATH
            with open(stop_file_path, 'w') as f:
                f.write('stop')
    
        return response_json
  
