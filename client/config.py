import os


class Config:
    NAME = "sim1"
    SERVER_URL = "127.0.0.1:5000"
    RUN_SCRIPT =  os.path.join(os.path.dirname(__file__), 'run_match.sh')
    STOP_FILE_PATH = os.path.expandvars('$HOME/testgames/stop.txt')
    TEMPORAL_DIR = os.path.expandvars('$HOME/testgames/tmp')
    LOG_DIR = os.path.expandvars('$HOME/testgames/log')
