import requests

def task_post_request(host_name,api_key):
    post_url = "http://127.0.0.1:5000/communication/api"

    # POST したいデータ
    data = {
        "host_name": host_name,
        "api_key": api_key
    }
    headers = {
        'x-api-key': api_key,
        'x-host-name': host_name
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
  
