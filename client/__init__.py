from communication.task_post import task_post_request
from communication.result_post import result_post_request
import signal
import sys
import time
import os

def signal_handler(sig, frame):
    print("処理を終わります")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

while True:
    response_from_task_post = task_post_request()
    print("サーバー受信を開始します！")
    time.sleep(3)

    if (response_from_task_post != None):
        print("サーバーに受信できました！")

        log_dir = '/home/fugakatayama/rcgame/client/log_data'
        file_paths = [os.path.join(log_dir, file) 
                      for file in os.listdir(log_dir) 
                      if os.path.isfile(os.path.join(log_dir, file))]

        response_from_result_post = result_post_request(response_from_task_post, file_paths)
        print("サーバーから受信:",response_from_result_post)
        time.sleep(5)
    else:
        print("サーバーから受信できませんでした！")
        time.sleep(5)

