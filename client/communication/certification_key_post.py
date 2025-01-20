import requests
import json
import random
import string

def certification_key_post_request(host_name):
    post_url = "http://127.0.0.1:5000/communication/certification"

    # ランダムな host_name を生成
    api_key = 'a'
    
    data = {
        "host_name": host_name,
        "api_key": api_key
    }

    # POST 送信
    response = requests.post(
        post_url,
        json=data  # データを JSON 形式で送信
    )

    print("certification_key_post_request response status:", response.status_code)
    print("certification_key_post_request response text:", response.text)
    return response.json()