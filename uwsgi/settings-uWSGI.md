# uWSGI設定のメモ

Apache2+uWSGIで動作させるまでの設定手順を記す．

公式資料
- https://flask.palletsprojects.com/en/stable/deploying/
- https://flask.palletsprojects.com/en/stable/deploying/uwsgi/


## uWSGIのインストール
```bash
source env/bin/activate
pip install pyuwsgi
```

実行テスト
```bash
uwsgi --http 127.0.0.1:8000 --master -p 4 -w rcgame_flask.app:app
```
ブラウザで http://127.0.0.1:8000 へアクセスして確認

## 設定ファイルの作成

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

ブラウザで http://127.0.0.1:8000 へアクセスして確認

## Apache2の設定

Apache で mod_proxy, mod_proxy_http, mod_proxy_uwsgi のモジュールを有効にする  
```bash
sudo a2enmod proxy proxy_http proxy_uwsgi
sudo systemctl restart apache2
```

Apache の VirtualHost 設定ファイルを作成または編集する。ここでは， /etc/apache2/sites-available/rcgamestats.conf として作成し，000-default.confを無効化する．新規作成せずにデフォルト設定ファイル群(000-default.conf, default-ssl.conf)を編集しても良い．
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

仮想ホストを有効化し Apache をリロードする
(000-default.confをそのまま使う場合はApacheのリロードのみでOK)
```bash
sudo a2dissite 000-default.conf
sudo a2ensite rcgamestats.conf
sudo systemctl reload apache2
```

### (optional) URLにプレフィックスをつける

プロジェクトの.env内でAPPLICATION_ROOTを設定する．（例: "/subdir"）
```.env
APPLICATION_ROOT = "/subdir"
```

Apacheの mod_headers モジュールを有効化する
```bash
sudo a2enmod headers
```

apacheの設定ファイルを修正
```apacheconf
<VirtualHost *:80>
    ServerName localhost
    # DocumentRoot は任意。静的ファイルがある場合など設定

    # ApacheがリバースプロキシとしてuWSGIのHTTPポートに転送する
    # Googleログインのコールバック対応のために ProxyPreserveHost On にしておく
    # プレフィックスを追加する場合は最後の'/'をつけておく．
    ProxyPreserveHost On
    ProxyPass /subdir/ http://127.0.0.1:5000/subdir/
    ProxyPassReverse /subdir/ http://127.0.0.1:5000/subdir/

    <Location /subdir>
        require all granted
        RequestHeader set X-Forwarded-Prefix /subdir/
    </Location>
</VirtualHost>
```

### (本番用)uWSGIをデーモンとして動作させる

本番運用時はsystemdでuWSGIをデーモンとして動作させる．
以下は /etc/systemd/system/rcgamestats_uwsgi.service として登録する場合の例．
"path-to"を自分の環境に合わせて編集する．

```ini
[Unit]
Description=uWSGI instance to serve rcgamestats Flask app
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path-to/rcgamestats
Environment="PATH=/path-to/rcgamestats/venv/bin"
ExecStart=/path-to/rcgamestats/venv/bin/uwsgi --ini uwsgi.ini

[Install]
WantedBy=multi-user.target
```

※UserとGroupは実際の運用環境に合わせて www-data などの適切なユーザーに設定する．
※データベースファイル，ログディレクトリ，ログファイルなどにUserとGroupの書き込みパーミッションが与えられていることを確認する．


サービスをリロードして起動、かつ自動起動設定を行う：
```
sudo systemctl daemon-reload  
sudo systemctl start rcgamestats_uwsgi  
sudo systemctl enable rcgamestats_uwsgi
```

動かない場合は以下でエラーログを確認する
```
sudo journalctl -u rcgamestats_uwsgi.service -f
```
