import requests
import json
import random
import string

def generate_random_host_name(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def send_post_request():
    post_url = "http://127.0.0.1:5000/communication/api"

    # ランダムな host_name を生成
    host_name = generate_random_host_name()

    # POST したいデータ
    data = {
        "host_name": host_name
    }

    # POST 送信
    response = requests.post(
        post_url,
        json=data  # データを JSON 形式で送信
    )

    return response.json()