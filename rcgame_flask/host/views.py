from datetime import datetime, timedelta
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
    return render_template("host/index.html", hosts=hosts)


@host.route("/<int:host_id>")
@login_required
def show_detail(host_id):
    """
    Show the host details.
    """
    host = Host.query.get_or_404(host_id)

    return render_template("host/detail.html", host=host)


def get_host_status(host):
    """
    Return the status of the host.
    """
    if host.assigned_match and host.assigned_match.processed == MatchStatus.IN_PROGRESS:
        threshold = timedelta(minutes=15)
        if host.assigned_match.left_team.synch_mode and host.assigned_match.right_team.synch_mode:
            threshold = timedelta(minutes=5)

        if (datetime.now() - host.assigned_match.start_time) < threshold:
            return "busy"
        else:
            return "stalled"

    if host.last_accessed_at and (datetime.now() - host.last_accessed_at) < timedelta(minutes=5):
        return "online"

    return "offline"


@host.app_context_processor
def inject_status_function():
    return dict(get_host_status=get_host_status)
