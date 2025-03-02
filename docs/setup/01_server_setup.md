# Server Setup Instruction

このドキュメントでは、Ubuntu 22.04 での環境構築手順について説明します。

## 1. 必要なパッケージのインストール

まず、Python3 および仮想環境を構築するために必要なパッケージをインストールします。

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

また、Apache や必要なモジュール（例：mod_wsgi）がある場合は、適宜インストールしてください。

---

## 2. Python仮想環境の構築

プロジェクトルート内に仮想環境を作成し、依存パッケージをインストールします。以下の例では、仮想環境の名前を `venv` としています。必要に応じて名前は変更してください。

```bash
python3 -m venv venv
```

作成した仮想環境をアクティベートします。

```bash
source venv/bin/activate
```

---

# 3. アプリケーション依存パッケージのインストール

仮想環境内で、プロジェクトの依存パッケージをインストールします。プロジェクトルートに配置されている `requirements.txt` を利用する場合は、以下のコマンドを実行してください。

```bash
pip install -r requirements.txt
```

必要に応じて、追加のパッケージもこのタイミングでインストールしてください。

---

## 4. .env ファイルの設定

プロジェクトルートに `.env` ファイルを作成し、環境変数を設定します。`.env.example` に雛形を用意していいます。以下は設定例です。
URLにプレフィックスをつけたい場合は、APPLICATION_ROOTを設定してください。プレフィックスをつけるとは、例えば `http://127.0.0.1:5000` ではなく `http://127.0.0.1:5000/rcgamestats` がルートになるようにすることを意味します（`APPLICATION_ROOT="/rcgamestats"`と設定する）。


```dotenv
# .env ファイル例
FLASK_APP=rcgame_flask.app:create_app

APPLICATION_ROOT="/"

# Flaskアプリ用シークレットキー設定
SECRET_KEY=your_secret_key
WTF_CSRF_SECRET_KEY=your_wtf_csrf_secret_key

# 管理者アカウント設定
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_API_KEY=admin_api_key_here

# Google OAuth設定（必要な場合）
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret

# Google Spreadsheet設定（必要な場合）
GOOGLE_DOC_ID=your_google_document_id
GOOGLE_KEY_PATH=your_google_document_key_filepath
```

※`.env` ファイルはプロジェクトルートに配置してください。実際の運用時には、機密情報の扱いにご注意ください。
※ 設定項目はプロジェクトの仕様に合わせて適宜変更してください。

---
## 5. その他の初期設定

データベース初期化時にユーザーとOAuth用メールアドレスを登録することができます。後からWebインタフェースでも追加できます。

default_users.csv に初期ユーザーをリストできます。ユーザー名、メールアドレス、ユーザーのタイプ(admin,user)をCSV形式で列挙してください

default_allowed_emails.csv にOAuth用メールアドレスをリストできます。メールアドレスとユーザーのタイプをCSV形式で列挙してください。
※OAuthログインはGoogleアカウントでのみ利用可能です。OAuthを利用するにはGoogle側で設定した上で、.envファイルにその内容を記入しておく必要があります。


---

## 6. データベースの初期化とマイグレーション

初回セットアップやデータベース構造の変更があった場合は、データベースの初期化およびマイグレーションを行います。
以下は Flask-Migrate を利用している場合の例です。

```bash
# 初回のみ
flask db init

# マイグレーションファイルの作成
flask db migrate -m "Initial migration"

# データベースのアップグレード（テーブル作成）
flask db upgrade
```

初期設定のデータ登録（管理者アカウントの登録、テスト用データの投入など）を自動で実行するためのシェルスクリプトも用意しています。
プロジェクトトップディレクトリで以下を実行してください。

```bash
./init_db.sh
```

※管理者アカウントの名称はデフォルトで "admin" となっています。変更する場合は、`.env` 内の `ADMIN_USERNAME` の値を更新してください。

---

## 7. ローカルで実行

LAN内で動かすだけならば、プロジェクトのルートで以下を実行すれば動作します。
```bash
flask run --host=0.0.0.0
```
Webブラウザで http://127.0.0.1:5000 (プレフィックスをつけている場合は http://127.0.0.1:5000/PREFIX ) へアクセスしてログイン画面が表示されれば成功です。


---

## 8. (optional) Google OAuth の設定

Google OAuth を利用した認証機能を用意しています。
通常のアカウントに対してはパスワードリマインド機能を用意していないため、Googleアカウントでの利用を推奨します。

[Google Cloud Console]((https://console.cloud.google.com/)) 上で以下の設定を行います。

1. OAuth同意画面 (上部検索ボックスで検索可能)
   1. Google Auth Platform が構成されていない場合は開始する
2. プロジェクト構成画面
   1. プロジェクト名 と 自分（達）への連絡用メールアドレス を入力
   2. 対象(User Type) -> 外部(External) 
   3. 連絡先情報 -> 自分のメールアドレス
   4. 同意して終了
3. OAuthクライアントを作成（OAuth クライアント ID の作成）
   1. アプリケーションの種類 -> ウェブアプリケーション
   2. 名前 -> プロジェクト名と同じで良い？
   3. 承認済みのJavaScript生成元 (仮入力)-> http://127.0.0.1:5000/PREFIX
   4. 承認済みのリダイレクトURI (仮入力)->  http://127.0.0.1:5000/PREFIX/auth/google/callback
   5. (外部公開アドレスが用意できているなら追加しておく)
   6. 作成 ボタンを押下
4. データアクセス（左サイドメニューから）
   1. スコープを追加または削除
      1. チェック -> Googleアカウントのメインのメールアドレスの参照
   2. Saveボタン押下
5. クライアント（左サイドメニューから）
   1. OAuth 2.0 クライアント ID 一覧画面 に作成したプロジェクトが表示される
   2. クライアントIDをコピーしておく
   3. クライアントシークレットをコピーしておく
   4. クライアントシークレットのJSONファイルをダウンロードして保管 client_secret_xxx.json
6. .env の GOOGLE_OAUTH_CLIENT_ID と GOOGLE_OAUTH_CLIENT_SECRET を設定する

---




 
