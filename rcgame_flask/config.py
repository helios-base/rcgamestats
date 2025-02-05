import os
from dotenv import load_dotenv

# プロジェクトのルートディレクトリにある .env ファイルを読み込む
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class Config:
    DOC_ID = os.getenv("DOC_ID", None)
    KEY_PATH = os.getenv("KEY_PATH", None)


config = Config()
