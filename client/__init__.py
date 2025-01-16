from communication.task_post import task_post_request
from communication.result_post import result_post_request
from communication.certification_key_post import certification_key_post_request
import signal
import sys
import time
import os
import random
import string

def generate_random_host_name(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def signal_handler(sig, frame):
    print("処理を終わります")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

host_name = generate_random_host_name()
api_key = certification_key_post_request(host_name)
print("host_name:",host_name)

if (api_key != None):
    while True:
        response_from_task_post = task_post_request(host_name)
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
else:
    print("認証失敗、プロダクトキーが違います")

