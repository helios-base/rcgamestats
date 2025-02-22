
import os
import time
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash
from flask import jsonify, request
from flask import Response
from flask import current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from authlib.integrations.base_client.errors import OAuthError
from rcgame_flask.app import db
from rcgame_flask.auth.decorators import admin_required
from rcgame_flask.auth.forms import LoginForm, UserRegistrationForm, PasswordChangeForm, EmailRegistrationForm
from rcgame_flask.auth.models import User, AllowedEmail, APIKey, UserType
from rcgame_flask.config import config

auth = Blueprint('auth', __name__, template_folder='templates', static_folder='static')


@auth.route('/')
def index():
    return render_template('auth/index.html')


@auth.route('/get_csrf_token')
def get_csrf_token():
    token = generate_csrf()
    print(f"CSRF Token: [{token}]")
    return jsonify({'csrf_token': token})


@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page
    """
    form = LoginForm()
    if form.validate_on_submit():
        username_or_email = form.username.data
        password = form.password.data

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email),
            User.auth_provider == 'local'
        ).first()

        if user and user.check_password(password):
            login_user(user)
            current_app.logger.info(f"User [{user.username}] logged in")
            return redirect(url_for("index"))

        flash("authentication failed")
        current_app.logger.info(f"User [{user.username}] login failed")

    use_google_login = current_app.config.get("GOOGLE_OAUTH_CLIENT_ID") and current_app.config.get("GOOGLE_OAUTH_CLIENT_SECRET")

    return render_template("auth/login.html", form=form, use_google_login=use_google_login)


@auth.route("/logout")
@login_required
def logout():
    """
    Logout
    """
    current_app.logger.info(f"User [{current_user.username}] logged out")
    logout_user()
    flash("logout done")   

    return redirect(url_for("auth.login"))



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
            current_app.logger.info(f"User [{current_user.username}] password change failed")
            return redirect(url_for("auth.change_password"))

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("password changed")
        current_app.logger.info(f"User [{current_user.username}] password changed")
        return redirect(url_for("index"))

    return render_template("auth/change_password.html", form=form)


#
# Google login
#


@auth.route("/login/google")
def login_google():
    """
    Login with Google
    """

    use_google_login = current_app.config.get("GOOGLE_OAUTH_CLIENT_ID") and current_app.config.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not use_google_login:
        flash("Google login is not enabled")
        current_app.logger.info("Google login is not enabled")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.login_google_callback", _external=True)
    return current_app.oauth.google.authorize_redirect(redirect_uri)


@auth.route("/login/google/callback")
def login_google_callback():
    """
    Google login callback
    """
    try:
        token = current_app.oauth.google.authorize_access_token()
        resp = current_app.oauth.google.get('https://www.googleapis.com/oauth2/v2/userinfo', token=token)
        user_info = resp.json()
        email = user_info['email']

        if not email:
            flash(f"GoogleLogin: No email")
            current_app.logger.error(f"GoogleLogin: No email")
            return redirect(url_for("auth.login"))

        allowed_email = AllowedEmail.query.filter_by(email=email).first()
        if not allowed_email:
            flash(f"[{email}] is not allowed to login.")
            current_app.logger.warning(f"GoogleLogin: [{email}] is not allowed to login.")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                username=user_info["email"],
                email=email,
                auth_provider="google",
                password='',
                type=allowed_email.type
            )
            db.session.add(user)
            db.session.commit()

            api_key = APIKey(
                key=APIKey.generate_api_key(),
                user_id=user.id,
                scope=allowed_email.type
            )
            db.session.add(api_key)
            db.session.commit()
            current_app.logger.info(f"GoogleLogin: Registered user [{user.username}]")

        login_user(user)
        current_app.logger.info(f"GoogleLogin: LoggedIn [{user.username}]")
        return redirect(url_for("index"))
    except OAuthError:
        flash(f"Exception: {OAuthError}")

    flash(f"GoogleLogin: Google account {email} cannot be verified")
    current_app.logger.warning(f"GoogleLogin: Google account {email} cannot be verified")
    return redirect(url_for("auth.login"))


#
# Admin actions
#

@auth.route("/admin/users", methods=["GET", "POST"])
@login_required
@admin_required
def show_users():
    """
    Show users
    """
    form = UserRegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        try:
            type = UserType(form.type.data)
        except ValueError:
            type = UserType.USER

        if username == "":
            username = email

        new_user = User(username=username, email=email, type=type)
        new_user.set_password(password)
        new_user.auth_provider = "local"
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            flash(f"Error: {e}")
            return redirect(url_for("auth.register"))

        if not AllowedEmail.query.filter_by(email=email).first():
            allowed_email = AllowedEmail(email=email, type=type)
            try:
                db.session.add(allowed_email)
                db.session.commit()
                current_app.logger.info(f"Registered email [{email}] as [{type.value}]")
            except Exception as e:
                flash(f"Error: {e}")

        api_key = APIKey(
            key=APIKey.generate_api_key(),
            user_id=new_user.id,
            scope=type
        )
        db.session.add(api_key)
        db.session.commit()

        flash(f"New user [{username}] registered")
        current_app.logger.info(f"Registered user [{username}] as [{type.value}]")

    users = User.query.all()
    return render_template("auth/users.html", users=users, form=form)


@auth.route("/admin/users/change_type", methods=["POST"])
@login_required
@admin_required
def change_user_type():
    """
    Change user type
    """
    user_id = request.form.get("user_id")
    if not user_id:
        flash("User ID is missing.", "error")
        return redirect(url_for("auth.show_users"))

    # print(f"Current user: {current_user.username}")
    # print(f"target User ID: {user_id}")
    user = User.query.get(user_id)
    if user:
        if user.email == current_user.email:
            flash(f"Cannot change own user type. mail={user.email}")
            current_app.logger.warning(f"Cannot change own user type. mail={user.email}")
        elif user.type == UserType.MASTER:
            flash("Cannot change the master user type")
            current_app.logger.warning("Cannot change the default admin user type")
        elif user.type == UserType.ADMIN and current_user.type != UserType.MASTER:
            flash("Cannot change the admin user type")
            current_app.logger.warning("Cannot change the admin user type")
        else:
            try:
                old_type = user.type
                if old_type == UserType.MASTER:
                    flash("Cannot change the master user type")
                    current_app.logger.warning("Cannot change the master user type")
                    return redirect(url_for("auth.show_users"))

                if old_type == UserType.USER:
                    new_type = UserType.ADMIN
                else:
                    new_type = UserType.USER

                user.type = new_type
                db.session.commit()
                flash(f"User [{user.username}] type changed from [{old_type.value}] to [{new_type.value}]")
                current_app.logger.info(f"Changed [{user.username}], from [{old_type.value}] to [{new_type.value}]")
            except ValueError:
                flash("Invalid user type")

    return redirect(url_for("auth.show_users"))


@auth.route("/admin/users/bulk_delete", methods=["POST"])
@login_required
@admin_required
def bulk_delete_users():
    """
    Bulk delete users
    """
    user_ids = request.form.getlist("user_ids")
    count = 0
    for user_id in user_ids:
        record = User.query.filter_by(id=user_id).first()
        if record:
            if record.email == current_user.email:
                flash("Cannot delete yourself")
                continue
            if record.type == UserType.MASTER:
                flash("Cannot delete master user")
                continue
            if record.type == UserType.ADMIN:
                if current_user.type != UserType.MASTER:
                    flash("Cannot delete admin user")
                    continue
            count += 1
            db.session.delete(record)
            current_app.logger.info(f"Deleting user [{record.username}]")
    db.session.commit()
    flash(f"Deleted {count} users")
    return redirect(url_for("auth.show_users"))


@auth.route("/admin/allowed_emails", methods=["GET", "POST"])
@login_required
@admin_required
def show_allowed_emails():
    """
    Show allowed emails
    """
    form = EmailRegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        try:
            type = UserType(form.type.data)
        except ValueError:
            type = UserType.USER
        if not AllowedEmail.query.filter_by(email=email).first():
            allowed_email = AllowedEmail(email=email, type=type)
            try:
                db.session.add(allowed_email)
                db.session.commit()
                flash(f"New email [{email}] registered as [{type.value}]")
                current_app.logger.info(f"Registered email [{email}] as [{type.value}]")
            except Exception as e:
                flash(f"Error: {e}")
        else:
            flash(f"Email [{email}] already exists")
            current_app.logger.warning(f"show_allowed_email: Email [{email}] already exists")

    emails = AllowedEmail.query.all()
    return render_template("auth/allowed_emails.html", emails=emails, form=form)


@auth.route("/admin/allowed_emails/bulk_delete", methods=["POST"])
@login_required
@admin_required
def bulk_delete_allowed_emails():
    """
    Bulk delete allowed emails
    """
    email_ids = request.form.getlist("email_ids")
    count = 0
    for email_id in email_ids:
        record = AllowedEmail.query.filter_by(id=email_id).first()
        if record:
            if record.email == current_user.email:
                flash("Cannot delete own email")
                continue
            count += 1
            db.session.delete(record)
            current_app.logger.info(f"Delete email [{record.email}]")
    db.session.commit()
    flash(f"Deleted {count} emails")
    return redirect(url_for("auth.show_allowed_emails"))


@auth.route("/admin/logs", methods=["GET"])
@login_required
@admin_required
def show_server_logs():
    """
    Show server logs
    """
    return render_template("auth/server_logs.html")


@auth.route("/admin/logs/stream", methods=["GET"])
@login_required
@admin_required
def stream_server_logs():
    """
    Streaming endpoint that yields new log lines similar to 'tail -f'
    """
    log_file = os.path.join(current_app.static_folder, "logs", "server.log")

    def generate():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                tail_lines = lines[-5:]
                for line in tail_lines:
                    yield f"data: {line}\n\n"
        except Exception as e:
            yield f"data: Error reading log: {e}\n\n"

        # Open the log file in read mode and seek to its end
        with open(log_file, "r", encoding="utf-8") as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    # No new data, wait a bit and retry
                    yield ": heartbeat\n\n"
                    time.sleep(1)
                    continue
                # send as Server-Sent Events format (data: <message>\n\n)
                # (see https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
                yield f"data: {line}\n\n"

    response = Response(generate(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    return response


#
# Dashboard
#


@auth.route("/dashboard")
@login_required
def dashboard():
    """
    Dashboard
    """
    # print(f"Current user: {current_user.username}")
    # print(f"API keys: {len(current_user.api_keys.all())}")
    # for key in current_user.api_keys:
    #     print(f"API key: {key.key}")
    return render_template("auth/dashboard.html")


@auth.route("/api_key")
@login_required
def api_keys():
    """
    API keys
    """
    return render_template("auth/api_keys.html", user=current_user)


#
# APIKey actions
#

@auth.route("/api_key/create", methods=["GET"])
def create_api_key():
    """
    Create API key
    """
    scope = current_user.type
    expires_in = None

    api_key = APIKey(
        key=APIKey.generate_api_key(),
        user_id=current_user.id,
        scope=scope,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None
    )
    db.session.add(api_key)
    db.session.commit()
    flash("API key created")
    current_app.logger.info(f"Created API key for user [{current_user.username}]")

    return redirect(url_for('auth.api_keys'))


@auth.route("/api_key/<int:key_id>/delete", methods=["POST"])
@login_required
def delete_api_key(key_id):
    """
    Delete API key
    """
    user_api_keys = current_user.api_keys.all()
    if len(user_api_keys) == 1:
        flash("At least one API key is required")
        return redirect(url_for("auth.api_keys"))

    api_key = APIKey.query.get(key_id)
    if api_key is None:
        flash("API key not found")
        return redirect(url_for("auth.api_keys"))

    db.session.delete(api_key)
    db.session.commit()
    flash("API key deleted")
    current_app.logger.info(f"Deleted API key for user [{current_user.username}]")
    return redirect(url_for("auth.api_keys"))


@auth.route("/admin/api_key")
@login_required
@admin_required
def admin_api_keys():
    """
    Admin API keys
    """
    users = User.query.all()
    return render_template("auth/admin_api_keys.html", users=users)


@auth.route("/admin/api_key/<int:key_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_api_key(key_id):
    """
    Delete API key
    """
    api_key = APIKey.query.get(key_id)
    if api_key is None:
        flash("API key not found")
        return redirect(url_for("auth.api_keys"))

    user = User.query.get(api_key.user_id)
    if user is None:
        flash("User not found")
        current_app.logger.warning(f"User not found for API key [{api_key.key}]")

    if user and user.is_admin:
        if user.id != current_user.id:
            flash("Cannot delete other admin user's API key")
            current_app.logger.warning(f"Cannot delete the API key of other admin user [{user.username}]")
            return redirect(url_for("auth.admin_api_keys"))
        elif len(user.api_keys.all()) == 1:
            flash("Cannot delete the only API key of the admin user")
            current_app.logger.warning(f"Cannot delete the only API key of the admin user [{user.username}]")
            return redirect(url_for("auth.admin_api_keys"))

    db.session.delete(api_key)
    db.session.commit()
    flash("API key deleted")
    current_app.logger.info(f"Deleted API key for user [{user.username}]")
    return redirect(url_for("auth.admin_api_keys"))
