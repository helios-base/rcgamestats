import requests
import json
import random
import string

def certification_key_post_request(host_name):
    post_url = "http://127.0.0.1:5000/communication/certification"

    # ランダムな host_name を生成
    product_key = 'a'
    
    data = {
        "host_name": host_name,
        "product_key": product_key
    }

    # POST 送信
    response = requests.post(
        post_url,
        json=data  # データを JSON 形式で送信
    )
    return response.json()