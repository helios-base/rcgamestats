import requests
import json
import random
import string

def task_post_request(host_name):
    post_url = "http://127.0.0.1:5000/communication/api"

    # POST したいデータ
    data = {
        "host_name": host_name
    }

    # POST 送信
    response = requests.post(
        post_url,
        json=data  # データを JSON 形式で送信
    )

    print("task_post_request response status:", response.status_code)
    print("task_post_request response text:", response.text)
    
    return response.json()