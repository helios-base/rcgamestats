# uWSGI設定のメモ

https://flask.palletsprojects.com/en/stable/deploying/uwsgi/

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
今回は /etc/apache2/sites-available/rcgamestats.conf として作成する．

```apacheconf
<VirtualHost *:80>
    ServerName localhost
    # DocumentRoot は任意。静的ファイルがある場合など設定

    # ApacheがリバースプロキシとしてuWSGIのHTTPポートに転送する
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    ErrorLog ${APACHE_LOG_DIR}/rcgamestats_error.log
    CustomLog ${APACHE_LOG_DIR}/rcgamestats_access.log combined
</VirtualHost>

```

仮想ホストを有効化し Apache を再起動する
```bash
sudo a2dissite 000-default.conf
sudo a2ensite rcgamestats.conf
sudo systemctl reload apache2
```

---

テスト中
rcgamestatsプレフィックスをつける
最初からソース内でプレフィックスをつけておくほうが無難か？

参考
https://qiita.com/katsuko0303/items/8d13654341859f5a9bbe


ConfigにAPPLICATION_ROOTを追加する．
ただし，これをやると通常時のログインができなくなってしまう．
```python
class Config:
    APPLICATION_ROOT= "/rcgamestats"
    SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")
```

app.pyの末尾に追記する
```python
app = create_app()
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
```

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
    ProxyPass /rcgamestats/ http://127.0.0.1:5000/
    ProxyPassReverse /rcgamestats/ http://127.0.0.1:5000/

    ErrorLog ${APACHE_LOG_DIR}/rcgamestats_error.log
    CustomLog ${APACHE_LOG_DIR}/rcgamestats_access.log combined

    <Location /rcgamestats>
        require all granted
        RequestHeader set X-Forwarded-Prefix /rcgamestats/
    </Location>
</VirtualHost>
```


他のやり方？
https://stackoverflow.com/questions/18967441/add-a-prefix-to-all-flask-routes

