import os


class Config:
    def __init__(self):
        self.SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:5000")
        self.HOST_NAME = os.getenv("HOST_NAME", "localhost")
        self.API_KEY = os.getenv("API_KEY", "unknown")
        self.GROUP_DIR = os.getenv("GROUP_DIR", "unknown")
        self.GROUP_NAME = os.getenv("GROUP_NAME", "unknown")
        self.LEFT_TEAM_NAME = os.getenv("LEFT_TEAM_NAME", "unknown")
        self.LEFT_TEAM_VERSION = os.getenv("LEFT_TEAM_VERSION", "")
        self.RIGHT_TEAM_NAME = os.getenv("RIGHT_TEAM_NAME", "unknown")
        self.RIGHT_TEAM_VERSION = os.getenv("RIGHT_TEAM_VERSION", "")
        self.DESCRIPTION = os.getenv("DESCRIPTION", None)

    def update_from_args(self, args):
        self.SERVER_URL = args.server_url
        self.HOST_NAME = args.host_name or self.HOST_NAME
        self.API_KEY = args.api_key
        self.GROUP_DIR = args.group_dir
        self.GROUP_NAME = args.group_name
        self.LEFT_TEAM_NAME = args.left_team_name
        self.LEFT_TEAM_VERSION = args.left_team_version or ""
        self.RIGHT_TEAM_NAME = args.right_team_name
        self.RIGHT_TEAM_VERSION = args.right_team_version or ""
        self.DESCRIPTION = args.description


config = Config()
