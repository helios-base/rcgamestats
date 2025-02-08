from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from rcgame_flask.app import db
from rcgame_flask.auth.forms import LoginForm, SignUpForm, PasswordChangeForm
from rcgame_flask.auth.models import User, APIKey

auth = Blueprint('auth', __name__, template_folder='templates', static_folder='static')


@auth.route('/')
def index():
    return render_template('auth/index.html')


@auth.route('/get_csrf_token')
def get_csrf_token():
    token = generate_csrf()
    print(f"CSRF Token: [{token}]")
    return jsonify({'csrf_token': token})


@auth.route("/create_api_key", methods=["POST"])
def create_api_key():
    user_id = request.json.get('user_id')
    scope = request.json.get('scope')
    expires_in = request.json.get('expires_in')  # 有効期限（秒）

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    api_key = APIKey(
        key=APIKey.generate_api_key(),
        user_id=user_id,
        scope=scope,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None
    )
    db.session.add(api_key)
    db.session.commit()

    return jsonify({'api_key': api_key.key})


@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page
    """
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user_record = User.query.filter_by(username=username).first()
        if user_record is not None and user_record.check_password(password):
            login_user(user_record)
            return redirect(url_for("index"))
        flash("authentication failed")

    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    """
    Logout
    """
    logout_user()
    flash("logout done")   

    return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    Register page
    """
    form = SignUpForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        flash("user registered")  
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    Change password
    """
    form = PasswordChangeForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("current password is incorrect")
            return redirect(url_for("auth.change_password"))

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("password changed")
        return redirect(url_for("index"))

    return render_template("auth/change_password.html", form=form)
