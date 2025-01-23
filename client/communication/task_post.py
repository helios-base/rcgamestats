import requests

def task_post_request(host_name,api_key):
    post_url = "http://127.0.0.1:5000/communication/api"

    # POST したいデータ
    data = {
        "host_name": host_name
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
    
    return response.json()