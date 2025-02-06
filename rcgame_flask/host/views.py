from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from rcgame_flask.app import db
from rcgame_flask.host.models import Host


host = Blueprint("host", __name__, template_folder="templates", url_prefix="/host")


@host.route("/")
@login_required
def index():
    """
    Show all hosts.
    """
    hosts = Host.query.all()
    return render_template("host/index.html", hosts=hosts)
