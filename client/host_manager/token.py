import os
from config import config


def load_token():
    host_token_path = os.path.expanduser(config.HOST_TOKEN_PATH)
    if os.path.exists(host_token_path):
        with open(host_token_path, "r") as f:
            return f.read().strip()
    return None


def save_token(token):
    if token is None:
        return False
    host_token_path = os.path.expanduser(config.HOST_TOKEN_PATH)
    with open(host_token_path, "w") as f:
        f.write(token)
    return True
