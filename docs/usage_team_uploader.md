[Top](README.md)
# How to use team_uploader

team_uploaderの使用方法を説明します．

## group_uploaderとは

チームバイナリのアーカイブを登録できるコンソールツールです。
以下の二種類を用意しています。
- api_team_uploader.py
- team_uploader.py


### api_team_uploader.py

adminアカウント用のAPIキーを用いてチームをアップロードするスクリプトです。
adminアカウント用のAPIキーが必要です。

#### 使用方法
```bash
pytyon api_uploade_team.py OPTIONS...
```
使用できるコマンドラインオプションは `--help`オプションで確認できます。
```bash
python api_team_uploder.py --help
```

### team_uploader.py

コンソールでログイン操作を行い、CSVファイルに列挙されたチーム情報を参照して、まとめてチームをアップロードするスクリプトです。

CSVファイルの各レコードは、チーム名、チームバージョン、synch_mode対応、アーカイブファイルパス、説明文 で構成されます。
CSVファイルの例:
```csv
team_name,version,synch_mode,archive_path,description
cyrus2024,rc2024,True,./teams/cyrus2024.tar.gz,"",
helios2024,rc2024,True,./teams/helios2024.tar.gz,""
yushan2024,rc2024,True,./teams/yushan2024.tar.gz,""
robocin2024,rc2024,True,./teams/robocin2024.tar.gz,""
```