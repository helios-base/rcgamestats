import os
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent

# load .env file in the root directory
#load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(root_dir / ".env", override=True)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(root_dir, 'instance', 'rcgamestats.sqlite')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", "my_wtf_csrf_secret_key")

    GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "")
    GOOGLE_KEY_PATH = os.getenv("GOOGLE_KEY_PATH", "")


config = Config()
