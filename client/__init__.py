from communication.task_post import task_post_request
from communication.result_post import result_post_request
from communication.create_user import create_user 
import signal
import sys
import time
import os
import random
import string

def signal_handler(sig, frame):
    print("処理を終わります")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

while True: 
    print("新規登録：１")
    print("登録済み：２")
    choice = input("選択してください: ")

    if choice in ['1', '１']:
        username = input("Enter a username: ")
        host_name, api_key = create_user(username)
        break  
    elif choice in ['2', '２']:
        host_name = input("Enter your host_name: ")
        api_key = input("Enter your API key: ")
        break 
    else:
        print("無効な選択です。もう一度選択してください。")

print("host_name:",host_name)

if (api_key != None):
    while True:
        response_from_task_post = task_post_request(host_name,api_key)
        print("サーバー受信を開始します！",response_from_task_post)
        time.sleep(3)

        if (response_from_task_post != None):
            print("サーバーに受信できました！")

            log_dir = '/home/fugakatayama/rcgame/client/log_data'
            file_paths = [os.path.join(log_dir, file) 
                          for file in os.listdir(log_dir) 
                          if os.path.isfile(os.path.join(log_dir, file))]

            response_from_result_post = result_post_request(response_from_task_post, file_paths,api_key)
            print("サーバーから受信:",response_from_result_post)
            time.sleep(5)
        else:
            print("サーバーから受信できませんでした！")
            time.sleep(5)
else:
    print("認証失敗、プロダクトキーが違います")

