from communication.task_post import task_post_request
from communication.result_post import result_post_request
from communication.create_user import create_user 
import requests
import signal
import sys
import time
import os

stop_file_path = '/home/fugakatayama/rcgame/client/condition/stop.txt'

def signal_handler(sig, frame):
    print("処理を終わります")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def create_user_or_login():
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
    return host_name, api_key

def main(host_name,api_key,stop_file_path):
    while True:
        try:
            response_from_task_post = task_post_request(host_name,api_key)
            if response_from_task_post and response_from_task_post.get('stop_check') == True:
                if os.path.exists(stop_file_path):
                    print("停止ファイルが見つかりました。処理を終わります")
                    time.sleep(5)
                    os.remove(stop_file_path)
                    break

            if response_from_task_post is not None and "error" in response_from_task_post:
                print(response_from_task_post)
                break

            print("サーバー受信を開始します！")

            time.sleep(3)

            if (response_from_task_post != None):
                print("サーバーに受信できました！")

                log_dir = '/home/fugakatayama/rcgame/client/log_data'
                file_paths = [os.path.join(log_dir, file) 
                              for file in os.listdir(log_dir) 
                              if os.path.isfile(os.path.join(log_dir, file))]

                response_from_result_post = result_post_request(response_from_task_post, file_paths,api_key,host_name)
                if response_from_result_post is not None and "error" in response_from_result_post:
                    print(response_from_result_post)
                    break

                print("サーバーから受信:",response_from_result_post)
                time.sleep(5)
            else:
                print("サーバーから受信できませんでした！")
                time.sleep(5)

        except requests.exceptions.RequestException as e:
            print(f"サーバーに接続できませんでした")
            print("10秒後に再試行します...")
            time.sleep(10)
    

host_name,api_key = create_user_or_login()
main(host_name,api_key,stop_file_path)