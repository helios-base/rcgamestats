import requests
from config import Config

def task_post_request(host_name,api_key):
    post_url = f"http://{Config.SERVER_URL}/communication/api"

    # POST したいデータ
    data = {
        "host_name": host_name,
        "api_key": api_key
    }
    headers = {
        'x-api-key': api_key,
        'X-CSRFToken': 'kwjer283n2k3gpiue9vrdfagb'
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
        if response_json.get('stop_check') == True:
            stop_file_path = '/home/fugakatayama/rcgame/client/condition/stop.txt'
            with open(stop_file_path, 'w') as f:
                f.write('stop')
    
        return response_json
  
