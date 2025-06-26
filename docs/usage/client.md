[Top](../README.md)
# How to use client

clientの設定手順・使用方法を説明します．

## clientとは

試合を実行するためのスクリプト群です。おおよそ以下のように動作します。
- 起動直後
  - サーバへ接続を試み，自身が実行されているホストを登録します
  - 登録に成功すると，サーバからIDとトークンが発行されます
  - 以降の通信にはそれらを使用します
- 実行中
  - 何もしなければ無限に動き続けます
  - 定期的にサーバと通信し、試合をリクエストします
  - 実行すべき試合が存在すれば、その試合を実行します
    - 試合実行に必要なチームバイナリを持っていない場合は、サーバにチームデータをリクエストします
    - 受信に成功すれば、チームバイナリを自動で展開します
    - チームバイナリの実行に必要な設定に関しては、clientは責任を持ちません 
  - 試合が正常終了すれば、試合結果をサーバへ送信します
  - 試合が異常終了した場合は、その試合の取り下げをサーバへ送信します

## 必要ライブラリ・ツール
  - Linux Environment (Ubuntu 22.04 is recommended)
  - Python3
  - [rcssserver](https://github.com/rcsoccersim/rcssserver)
  - (optional) [librcsc](https://github.com/helios-base/librcsc)
  - (optional) [rcg2data](https://github.com/hidehisaakiyama/rcg2data)
  - (optional) cpufrequtils

Linux環境での実行を想定しています。RoboCupサッカーシミュレータを実行できる環境が必須です。

librcscがインストールされていると、ログファイルの整合性チェックが自動で実行されます。また、SV形式に変換した試合ログが保存されます。

rcg2dataがインストールされていると、試合ごとのイベントデータなどのCSVファイルが保存されます。

cpufrequtils(cpufreq-set)を実行可能な状態にしておくと、実行効率が上がります。

## 初期設定

client/.env.exampleを参考にして client/.env ファイルを作成してください。API_KEYとSERVER_URLの設定は必ず必要です。その他、チームバイナリやログファイルを保存する場所の指定も可能です。

loganalyzer3を使用したい場合は, 
rcgamestats/client/setuploganalyzer3.sh を実行してからクライアントを起動してください．

## 実行方法

```bash
python run.py
```

## 停止方法

Ctrl-C(SIGINT)による割り込みで停止できます。シミュレータを実行途中であっても強制終了させ、その試合をキャンセルします。

バックグラウンドで実行している場合：
- 方法1（シミュレータもすぐに止めたい場合）: `kill -INT <pid>`のようにSIGINTシグナルでkillする。`pkill -INT -f run.py`がおそらく最も簡単。
- 方法2（シミュレータの終了まで待ってから止めたい場合）: .envの STOP_FILE_PATH で指定しているファイルを作成する

## cpufreq-setをsudoなしで実行するための設定

Ubuntu Linux環境を想定して説明します。

設定ファイルを編集します。エディタはviになります。

```bash
sudo visudo
```

以下の部分を探し、実行するユーザー名と実行したいコマンドを記入してください。以下の例では、ユーザーは`robocup`、実行するコマンドは `/usr/bin/cpufreq-set` です。
```
# Allow members of group sudo to execute any command
%sudo   ALL=(ALL:ALL) ALL
robocup    ALL=NOPASSWD: /usr/bin/cpufreq-set
```
この設定によって、robocupアカウントはcpufreq-setをsudoなしで実行できるようになります。