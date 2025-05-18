[Top](../README.md)
# How to use group_uploader

clientの使用方法を説明します．

## group_uploaderとは

試合ログ一式を用いてグループを後から追加することができるコンソールツールです。rcgamestatsの機能で実行していない試合ログからでも登録できます。ただし、チーム登録はバージョン無しで行われます。


## 使用方法

### もっとも簡単な方法
```bash
./submit.sh LOG_DIR
```
ただし，接続先アドレスなどはsubmit.shの先頭付近にある変数の値を変更しなければなりません。

例:
```bash
./submit.sh /log/20250220-183344-helios2024-cyrus2024
```

その他の仕様:
- オプションで与えるディレクトリ名は "YYYYmmdd-HHMMSS-TEAM1-TEAM2" の書式を想定
- グループ名はオプションで与えたディレクトリ名になる
- 左右のチーム名はディクトリ名から切り出されて使用される

### 詳細なオプションを与える方法
```bash
python submit.py OPTTIONS...
```
例:
```bash
python submit.py --server-url http://127.0.0.1:5000 \
 --api-key xxxxx \
 --group-dir ./log/20250220-183344-helios2024-cyrus2024 \
 --group-name 20250220-183344-helios2024-cyrus2024 \
 --left-team-name helios2024 --left-team-version v1 \
 --right-team-name cyrus2024 --right-team-version v1
```

または、 group_uploader/.env ファイルを作成しておくと、その内容が参照されます。使用できる変数は group_uploader/.env.example を参考にしてください。
