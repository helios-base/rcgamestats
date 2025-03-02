import os
from config import config


def load_token():
    host_token_path = os.path.expanduser(config.HOST_TOKEN_PATH)
    if os.path.exists(host_token_path):
        with open(host_token_path, "r") as f:
            try:
                return int(f.readline().strip()), f.readline().strip()
            except ValueError:
                return None, None
    return None, None


def save_token(host_id, token):
    if host_id is None:
        return False
    if token is None:
        return False
    host_token_path = os.path.expanduser(config.HOST_TOKEN_PATH)
    with open(host_token_path, "w") as f:
        f.write(f"{host_id}\n{token}")
    return True
