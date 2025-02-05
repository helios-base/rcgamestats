from flask import Blueprint, render_template, request, redirect, url_for, flash
from rcgame_flask.models import db
from rcgame_flask.models import user
from rcgame_flask.forms import LoginForm, SignUpForm
from flask_login import login_user, logout_user, login_required

bp = Blueprint('auth', __name__, url_prefix='/auth')

# ログイン（Form使用）
@bp.route("/login", methods=["GET", "POST"])
def login():
    # Formインスタンス生成
    form = LoginForm()
    if form.validate_on_submit():
        # データ入力取得
        username = form.username.data
        password = form.password.data
        # 対象User取得
        user_record = user.query.filter_by(username=username).first()
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
@bp.route("/logout")
@login_required
def logout():
    # 現在ログインしているユーザーをログアウトする
    logout_user()
    # フラッシュメッセージ
    flash("ログアウトしました")   
    # 画面遷移
    return redirect(url_for("auth.login"))

# サインアップ（Form使用）
@bp.route("/register", methods=["GET", "POST"])
def register():
    # Formインスタンス生成
    form = SignUpForm()
    if form.validate_on_submit():
        # データ入力取得
        username = form.username.data
        password = form.password.data
        # モデルを生成
        new_user = user(username=username)
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