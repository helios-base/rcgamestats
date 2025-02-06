from communication.task_post import task_post_request
from communication.result_post import result_post_request
from communication.create_user import create_user 
from config import Config
from api_key import API_KEY
import pandas as pd
import argparse
import requests
import signal
import sys
import shutil
import time
import os

def signal_handler(sig, frame):
    with open(Config.STOP_FILE_PATH, 'w') as f:
        f.write('Stop signal received.')
    print("stop信号を検知しました。今の処理を完了した後に終了します")

#def signal_handler(sig, frame):
 #   print("処理を終わります")
  #  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


# def create_user_or_login():
#     while True: 
#         print("新規登録：１")
#         print("登録済み：２")
#         choice = input("選択してください: ")

#         if choice in ['1', '１']:
#             username = input("Enter a username: ")
#             host_name, api_key = create_user(username)
#             break  
#         elif choice in ['2', '２']:
#             host_name = input("Enter your host_name: ")
#             api_key = input("Enter your API key: ")
#             break 
#         else:
#             print("無効な選択です。もう一度選択してください。")

#     print("host_name:",host_name)  
#     return host_name, api_key


def run_game(left_team, right_team, log_file_name):
    print("run_game")
    print("... left_team:",left_team)
    print("... right_team:",right_team)
    print("... log_file_name:",log_file_name)
    os.system(f"{Config.RUN_SCRIPT} {left_team} {right_team} {Config.LOG_DIR} {log_file_name}")


def get_score_from_result_file(result_csv):
    left_score = 0
    right_score = 0
    # 'left socore'と'right score'の最初のレコードの値を取得
    if os.path.exists(result_csv):
        # ヘッダの列名のカンマ周辺の空白を除去してデータフレームを作る
        df = pd.read_csv(result_csv, skipinitialspace=True)
        if df.empty:
            print("result.csv is empty")
            return left_score, right_score
        left_score = df['left score'][0]
        right_score = df['right score'][0]

    return left_score, right_score


def main(host_name,api_key):
    while True:
        try:
            for file in os.listdir(Config.TEMPORAL_DIR):
                file_path = os.path.join(Config.TEMPORAL_DIR, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    
            if os.path.exists(Config.STOP_FILE_PATH):
                print("処理を終わります")
                os.remove(Config.STOP_FILE_PATH)
                break

            response_from_task_post = task_post_request(host_name,api_key)

            if response_from_task_post is not None and "error" in response_from_task_post:
                print(response_from_task_post)
                break

            print("サーバー受信を開始します！")
            time.sleep(3)

            if response_from_task_post is not None:

                run_game(response_from_task_post.get('left_team'),
                         response_from_task_post.get('right_team'),
                         response_from_task_post.get('log_file_name'))
 
                print("Finished the match!")
                result_csv = os.path.join(Config.LOG_DIR, response_from_task_post.get('log_file_name') + ".csv")
                left_score, right_score = get_score_from_result_file(result_csv)
                response_from_task_post["left_score"] = left_score
                response_from_task_post["right_score"] = right_score

                file_paths = [os.path.join(Config.LOG_DIR, file) 
                              for file in os.listdir(Config.LOG_DIR) 
                              if os.path.isfile(os.path.join(Config.LOG_DIR, file))]

                response_from_result_post = result_post_request(response_from_task_post, file_paths, api_key, host_name)
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
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send result post request.')
    parser.add_argument('--server_url', type=str, default=Config.SERVER_URL, help='Server URL')
    parser.add_argument('--name', type=str, default=Config.NAME, help='Host Name')
    args = parser.parse_args()

    if args.server_url:
        Config.SERVER_URL = args.server_url

    if args.name:
        Config.NAME = args.name

    if os.path.exists(Config.TEMPORAL_DIR):
        shutil.rmtree(Config.TEMPORAL_DIR)
    os.makedirs(Config.TEMPORAL_DIR)

    if not os.path.exists(Config.LOG_DIR):
        os.makedirs(Config.LOG_DIR)

    #host_name, api_key = create_user_or_login()
    main(Config.NAME, API_KEY)