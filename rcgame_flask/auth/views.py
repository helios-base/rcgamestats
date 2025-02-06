from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required
from flask_wtf.csrf import generate_csrf
from rcgame_flask.app import db
from rcgame_flask.auth.forms import LoginForm, SignUpForm
from rcgame_flask.auth.models import User

auth = Blueprint('auth', __name__, template_folder='templates', static_folder='static')


@auth.route('/')
def index():
    return render_template('auth/index.html')


@auth.route('/get_csrf_token')
def get_csrf_token():
    token = generate_csrf()
    #print(f"CSRF Token: {token}")
    return jsonify({'csrf_token': token})


@auth.route("/login", methods=["GET", "POST"])
def login():
    # ログイン（Form使用）
    # Formインスタンス生成
    form = LoginForm()
    if form.validate_on_submit():
        # データ入力取得
        username = form.username.data
        password = form.password.data
        # 対象User取得
        user_record = User.query.filter_by(username=username).first()
        # 認証判定
        if user_record is not None and user_record.check_password(password):
            # 成功
            # 引数として渡されたuserオブジェクトを使用して、ユーザーをログイン状態にする
            login_user(user_record)
            # 画面遷移
            return redirect(url_for("index"))
        # 失敗
        flash("認証不備です")
    # GET時
    # 画面遷移
    return render_template("auth/login.html", form=form)


# ログアウト
@auth.route("/logout")
@login_required
def logout():
    # 現在ログインしているユーザーをログアウトする
    logout_user()
    # フラッシュメッセージ
    flash("ログアウトしました")   
    # 画面遷移
    return redirect(url_for("auth.login"))


# サインアップ（Form使用）
@auth.route("/register", methods=["GET", "POST"])
def register():
    # Formインスタンス生成
    form = SignUpForm()
    if form.validate_on_submit():
        # データ入力取得
        username = form.username.data
        password = form.password.data
        # モデルを生成
        new_user = User(username=username)
        # パスワードハッシュ化
        new_user.set_password(password)
        # 登録処理
        db.session.add(new_user)
        db.session.commit()
        # フラッシュメッセージ
        flash("ユーザー登録しました")  
        # 画面遷移 
        return redirect(url_for("auth.login"))
    # GET時
    # 画面遷移
    return render_template("auth/register.html", form=form)