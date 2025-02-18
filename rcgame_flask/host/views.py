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
    print(hosts)
    for host in hosts:
        print(host.name)
    return render_template("host/index.html", hosts=hosts)


@host.route("/<int:host_id>")
@login_required
def show_detail(host_id):
    """
    Show the host details.
    """
    host = Host.query.get_or_404(host_id)

    matches = Match.query.filter_by(host_name=host.name, processed=MatchStatus.COMPLETED).all()
    total_matches = len(matches)
    total_times = sum([match.end_time - match.start_time for match in matches], timedelta(0))
    total_seconds = int(total_times.total_seconds())
    average_seconds = int(total_times.total_seconds() / total_matches)
    # hours = total_seconds // 3600
    # minutes = (total_seconds % 3600) // 60
    # seconds = total_seconds % 60

    # time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return render_template("host/detail.html", host=host, total_matches=total_matches, total_seconds=total_seconds, average_seconds=average_seconds)
