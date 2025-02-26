# uWSGI設定のメモ

https://flask.palletsprojects.com/en/stable/deploying/
https://flask.palletsprojects.com/en/stable/deploying/uwsgi/


---
source env/bin/activate

---
```bash
pip install pyuwsgi
```
---
実行テスト
```bash
# uwsgi --http 127.0.0.1:8000 --master -p 4 -w "rcgame_flask.app:create_app()"
uwsgi --http 127.0.0.1:8000 --master -p 4 -w rcgame_flask.app:app
```
ブラウザで http://127.0.0.1:8000 へアクセスしてみる

---

uwsgi.ini を作成
```ini
[uwsgi]
; Flaskアプリケーションのモジュール。例：rcgame_flask/app.py 内の app インスタンス
module = rcgame_flask.app:app

; HTTPモードで127.0.0.1:5000でリッスン（Apacheからリバースプロキシ予定）
http = 127.0.0.1:5000

; マスタープロセスの起動（推奨設定）
master = true

; ワーカープロセス数（必要に応じて調整）
processes = 5

; スレッド数（各プロセスあたり）
threads = 2

; 終了時にソケットファイルなどの一時ファイルをクリーンアップ
vacuum = true

; TERMシグナル時にきちんと終了する
die-on-term = true
```

iniファイルでの実行テスト
```bash
uwsgi --ini uwsgi.ini
```

ブラウザで http://127.0.0.1:8000 へアクセスしてみる

---

Apache で以下のモジュールを有効にする  
```bash
sudo a2enmod proxy proxy_http proxy_uwsgi
sudo systemctl restart apache2
```

Apache の VirtualHost 設定ファイルを作成または編集する。
今回は /etc/apache2/sites-available/rcgamestats.conf として作成し，000-default.confを無効化する．
80番ポートですべてまとめて動かすなら 000-default.conf を編集する．


```apacheconf
<VirtualHost *:80>
    ServerName localhost
    # DocumentRoot は任意。静的ファイルがある場合など設定

    # ApacheがリバースプロキシとしてuWSGIのHTTPポートに転送する
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    # 独自のエラーログを作る場合
    # ErrorLog ${APACHE_LOG_DIR}/rcgamestats_error.log
    # CustomLog ${APACHE_LOG_DIR}/rcgamestats_access.log combined
</VirtualHost>

```

仮想ホストを有効化し Apache を再起動する
```bash
sudo a2dissite 000-default.conf
sudo a2ensite rcgamestats.conf
sudo systemctl reload apache2
```

---

URLにプレフィックスをつける

プロジェクトの.env内でAPPLICATION_ROOTを設定する．（例: "/subdir"）

Apacheのモジュールを有効化する
```
sudo a2enmode headers
```

apacheの設定ファイルを修正
```apacheconf
<VirtualHost *:80>
    ServerName localhost
    # DocumentRoot は任意。静的ファイルがある場合など設定

    # ApacheがリバースプロキシとしてuWSGIのHTTPポートに転送する
    # 最後の'/'をつけておく
    ProxyPass /rcgamestats/ http://127.0.0.1:5000/rcgamestats/
    ProxyPassReverse /rcgamestats/ http://127.0.0.1:5000/rcgamestats/

    <Location /rcgamestats>
        require all granted
        RequestHeader set X-Forwarded-Prefix /rcgamestats/
    </Location>
</VirtualHost>
```
