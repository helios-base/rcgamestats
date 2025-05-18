import os
import socket
from pathlib import Path
from dotenv import load_dotenv
from distutils.util import strtobool


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
    API_KEY = os.getenv("API_KEY", "")
    HOST_NAME = os.getenv("HOST_NAME") or socket.gethostname()
    HOST_TOKEN_PATH = os.path.expanduser(os.getenv("HOST_TOKEN_PATH", "~/client/host_token.txt"))
    SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:5000")
    TEAM_DIR = os.path.expanduser(os.getenv("TEAM_DIR", "~/client/teams"))
    STOP_FILE_PATH = os.path.expanduser(os.getenv("STOP_FILE_PATH", "~/client/stop.txt"))
    TEMPORAL_DIR = os.path.expanduser(os.getenv("TEMPORAL_DIR", "~/client/tmp"))
    LOG_DIR = os.path.expanduser(os.getenv("LOG_DIR", "~/client"))
    USE_RCG2CSV = bool(strtobool(os.getenv("USE_RCG2CSV", "false")))
    USE_RCG2DATA = bool(strtobool(os.getenv("USE_RCG2DATA", "false")))
    CHANGE_CPUFREQ = bool(strtobool(os.getenv("CHANGE_CPUFREQ", "true")))
    INITIAL_SLEEP_TIME = get_env_int("INITIAL_SLEEP_TIME", 5)
    MAX_SLEEP_TIME = min(get_env_int("MAX_SLEEP_TIME", 60), 60)


config = Config()
