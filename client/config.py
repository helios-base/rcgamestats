import os
import subprocess
import socket
from pathlib import Path
from dotenv import load_dotenv


def get_env_int(var_name, default_value):
    """
    Get an environment variable and convert it to an integer.
    If the conversion fails, return the default value.
    """
    value = os.getenv(var_name, default_value)
    try:
        return int(value)
    except ValueError:
        print(f"Warning: Environment variable {var_name} is not a valid integer. Using default value {default_value}.")
        return default_value


# load .env file in the root directory
root_dir = Path(__file__).resolve().parent
load_dotenv(root_dir / ".env")


class Config:
    API_KEY = os.getenv("API_KEY", "unknown")
    # HOST_NAME = os.getenv("HOST_NAME") or get_hostname()
    HOST_NAME = os.getenv("HOST_NAME") or socket.gethostname()
    SERVER_URL = os.getenv("SERVER_URL", "127.0.0.1:5000")
    # RUN_SCRIPT =  os.path.join(os.path.dirname(__file__), 'match_manager', 'run_match.sh')
    TEAM_DIR = os.path.expanduser(os.getenv("TEAM_DIR", "~/rcgamestats/teams"))
    STOP_FILE_PATH = os.path.expanduser(os.getenv("STOP_FILE_PATH", "~/rcgamestats/stop.txt"))
    TEMPORAL_DIR = os.path.expanduser(os.getenv("TEMPORAL_DIR", "~/rcgamestats/tmp"))
    LOG_DIR = os.path.expanduser(os.getenv("LOG_DIR", "~/rcgamestats/log"))
    SLEEP_TIME = get_env_int("SLEEP_TIME", 5)
    MAX_SLEEP_TIME = min(get_env_int("MAX_SLEEP_TIME", 60), 60)


config = Config()
