import os
import sys
import fcntl
import time
import random
import signal
import logging
from logging.handlers import RotatingFileHandler
import match_manager
import team_manager
import host_manager
from config import config


LOCK_FILE = '/tmp/rcgamestats_client.lock'
lock_file = open(LOCK_FILE, 'w')
try:
    fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("Another instance is running. Exiting.")
    sys.exit(0)


# logging settings
logger = logging.getLogger("client")


def init_logging():
    logger.setLevel(logging.INFO)

    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)
    log_file = os.path.join(config.LOG_DIR, "client.log")
    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    # formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s in %(filename)s:%(lineno)d")
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def signal_handler(signal, frame):
    with open(config.STOP_FILE_PATH, "w") as f:
        f.write("Stop signal received.")
    # logger.info("Signal detected. The process will be finished after the current process is completed.")
    logger.info("Signal detected. The process will be finished.")


signal.signal(signal.SIGINT, signal_handler)


def interruptable_sleep(duration):
    end_time = time.time() + duration
    while True:
        if os.path.exists(config.STOP_FILE_PATH):
            logger.info("Stop file exists. The process will be finished.")
            break
        current_time = time.time()
        if current_time >= end_time:
            break
        sleep_time = end_time - current_time
        sleep_time = min(max(0, sleep_time), 5)
        time.sleep(sleep_time)


def create_directories():
    if not os.path.exists(config.TEAM_DIR):
        os.makedirs(config.TEAM_DIR)
    if not os.path.exists(config.TEMPORAL_DIR):
        os.makedirs(config.TEMPORAL_DIR)
    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)


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
        logger.error("(check_download_teams) No left team version.")
        return False
    if match.right_team_version == "":
        logger.error("(check_download_teams) No right team version.")
        return False

    # check or download left team
    if not team_manager.exist_team(match.left_team_name, match.left_team_version):
        if not team_manager.download_team(match.left_team_name, match.left_team_version):
            return False
        if not team_manager.exist_team(match.left_team_name, match.left_team_version):
            logger.error("(check_download_teams) No left team.")
            return False

    # check or download right team
    if not team_manager.exist_team(match.right_team_name, match.right_team_version):
        if not team_manager.download_team(match.right_team_name, match.right_team_version):
            return False
        if not team_manager.exist_team(match.right_team_name, match.right_team_version):
            logger.error("(check_download_teams) No right team.")
            return False

    return True


# def check_teams(match):
#     max_retries = 3
#     retry_delay = 5
#     for i in range(max_retries):
#         if check_download_teams(match):
#             return True
#         logger.warning("Failed to download teams.")
#         logger.info(f"Sleep for {retry_delay} seconds before retrying to download teams.")
#         time.sleep(retry_delay)
#     return False


def check_or_register_host():
    if not host_manager.register_host():
        return False
    return True


def main():
    if not config.API_KEY:
        print("no API_KEY")
        return
    remove_stop_file()

    if not check_or_register_host():
        logger.error("Failed to load host_token or register host.")
        return

    try:
        create_directories()
    except Exception as e:
        logger.error(f"Failed to create directories. {e}")
        return

    initial_sleep = config.INITIAL_SLEEP_TIME
    max_sleep = config.MAX_SLEEP_TIME
    current_sleep = initial_sleep

    try:
        while True:
            if os.path.exists(config.STOP_FILE_PATH):
                logger.info("Stop file exists. The process finished.")
                break

            match, error_type = match_manager.request_match()

            if match:
                logger.info(f">>>> Received {match.group_name}/{match.index}")
                remove_temporal_files()

                if check_download_teams(match):
                    if match.run():
                        try:
                            match_manager.submit_result(match)
                        except Exception as e:
                            logger.error(f"Failed to submit result for match {match.group_name}/{match.index}: {e}")
                    else:
                        match_manager.decline_match(match)
                    logger.info(f"<<<< Finished {match.group_name}/{match.index}")
                    current_sleep = initial_sleep
                else:
                    match_manager.decline_match(match)
                    logger.error("Failed to download teams.")
            else:
                if error_type == "request_error" or error_type == "unknown_error" or error_type == "http_error":
                    logger.error("Request error. Retry.")
                    current_sleep = min(current_sleep * 1.5, max_sleep)
                elif error_type == "host_not_found":
                    logger.error("Host not found. Register host again.")
                    if not check_or_register_host():
                        logger.error("Failed to load host_token or register host.")
                        break
                    current_sleep = initial_sleep
                else:
                    current_sleep = min(current_sleep * 1.5, max_sleep)

            jitter = random.uniform(0.8, 1.2)
            adjusted_sleep = min(max(initial_sleep, current_sleep * jitter), max_sleep + 10)
            logger.info(f"Sleep for {round(adjusted_sleep, 1)} seconds.")
            interruptable_sleep(adjusted_sleep)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    init_logging()
    main()
    logger.info("The process finished.")
    lock_file.close()
    os.remove(LOCK_FILE)
