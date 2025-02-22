import os
import time
import signal
import match_manager
import team_manager
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


def remove_stop_file():
    if os.path.exists(config.STOP_FILE_PATH):
        os.remove(config.STOP_FILE_PATH)


def check_download_teams(match):
    if match.left_team_version == "":
        print("(check_download_teams) No left team version.")
        return False
    if match.right_team_version == "":
        print("(check_download_teams) No right team version.")
        return False

    if not team_manager.exist_team(match.left_team_name, match.left_team_version):
        if not team_manager.download_team(match.left_team_name, match.left_team_version):
            return False
    if not team_manager.exist_team(match.right_team_name, match.right_team_version):
        if not team_manager.download_team(match.right_team_name, match.right_team_version):
            return False

    if not team_manager.exist_team(match.left_team_name, match.left_team_version):
        print("(check_download_teams) No left team.")
        return False

    if not team_manager.exist_team(match.right_team_name, match.right_team_version):
        print("(check_download_teams) No right team.")
        return False

    return True


def main():
    remove_stop_file()
    create_temporal_dir()

    initial_sleep = config.SLEEP_TIME
    max_sleep = config.MAX_SLEEP_TIME
    current_sleep = initial_sleep

    while True:
        if os.path.exists(config.STOP_FILE_PATH):
            print("Stop file exists. The process will be finished.")
            break

        remove_temporal_files()
        match = match_manager.request_match()

        if match:
            print("RECV:", match)
            while not check_download_teams(match):
                print("Failed to download teams.")
                match_manager.decline_match(match)
                print("Sleep for", initial_sleep, "seconds.")
                time.sleep(initial_sleep)
                continue

            if match.run():
                match_manager.submit_result(match)
            else:
                match_manager.decline_match(match)

            current_sleep = initial_sleep
        else:
            current_sleep = min(current_sleep * 2, max_sleep)

        print("Sleep for", current_sleep, "seconds.")
        time.sleep(current_sleep)


if __name__ == "__main__":
    main()
