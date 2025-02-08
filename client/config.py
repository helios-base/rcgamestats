import os
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent

# load .env file in the root directory
load_dotenv(root_dir / ".env")


class Config:
    HOST_NAME = os.getenv("HOST_NAME", "unknown")
    SERVER_URL = os.getenv("SERVER_URL", "127.0.0.1:5000")
    RUN_SCRIPT =  os.path.join(os.path.dirname(__file__), 'run_match.sh')
    STOP_FILE_PATH = os.getenv("STOP_FILE_PATH", os.path.expandvars('$HOME/rcgamestats/stop.txt'))
    TEMPORAL_DIR = os.getenv("TEMPORAL_DIR", os.path.expandvars('$HOME/rcgamestats/tmp'))
    LOG_DIR = os.getenv("LOG_DIR", os.path.expandvars('$HOME/rcgamestats/log'))


config = Config()
