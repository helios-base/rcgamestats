from datetime import timedelta
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from rcgame_flask.app import db
from rcgame_flask.host.models import Host
from rcgame_flask.group.models import Match, MatchStatus


host = Blueprint("host", __name__, template_folder="templates", url_prefix="/host")


@host.route("/")
@login_required
def index():
    """
    Show all hosts.
    """
    hosts = Host.query.all()
    for host in hosts:
        if host.assigned_match:
            print(f"Host: {host.name}, {host.assigned_match.processed}")
    return render_template("host/index.html", hosts=hosts)


@host.route("/<int:host_id>")
@login_required
def show_detail(host_id):
    """
    Show the host details.
    """
    host = Host.query.get_or_404(host_id)

    return render_template("host/detail.html", host=host)
