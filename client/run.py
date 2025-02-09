import os
import time
import signal
import match_manager
from config import config


def signal_handler(signal, frame):
    with open(config.STOP_FILE_PATH, "w") as f:
        f.write("Stop signal received.")
    print(
        "Signal detected. The process will be finished after the current process is completed."
    )


signal.signal(signal.SIGINT, signal_handler)


def create_temporal_dir():
    if not os.path.exists(config.TEMPORAL_DIR):
        os.makedirs(config.TEMPORAL_DIR)


def remove_temporal_files():
    for file in os.listdir(config.TEMPORAL_DIR):
        file_path = os.path.join(config.TEMPORAL_DIR, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


def create_log_dir(group_name):
    log_dir = os.path.join(config.LOG_DIR, group_name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def remove_stop_file():
    if os.path.exists(config.STOP_FILE_PATH):
        os.remove(config.STOP_FILE_PATH)


def main():
    remove_stop_file()
    create_temporal_dir()

    while True:
        if os.path.exists(config.STOP_FILE_PATH):
            print("Stop file exists. The process will be finished.")
            break

        remove_temporal_files()
        match = match_manager.request_match()
        if match:
            print("RECV:", match)
            match.run()
            match_manager.submit_result(match)

        print("Sleep for", config.SLEEP_TIME, "seconds.")
        time.sleep(config.SLEEP_TIME)

if __name__ == "__main__":
    main()
