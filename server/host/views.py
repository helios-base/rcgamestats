from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for
from flask import flash
from flask_login import login_required
from ..app import db
from ..auth.decorators import admin_required
from ..group.models import Match, MatchStatus
from .models import Host


host = Blueprint("host", __name__, template_folder="templates", url_prefix="/host")


#
# Helper functions
#


def get_host_status(host):
    """
    Return the status of the host.
    """
    match = Match.query.get(host.assigned_match_id)
    if match and match.status == MatchStatus.IN_PROGRESS:
        threshold = timedelta(minutes=15)
        if match.left_team.synch_mode and match.right_team.synch_mode:
            threshold = timedelta(minutes=5)

        if (datetime.now() - match.start_time) < threshold:
            return "busy"
        else:
            return "stalled"

    if host.last_accessed_at and (datetime.now() - host.last_accessed_at) < timedelta(minutes=5):
        return "online"

    return "offline"


#
# Context processors
#


@host.app_context_processor
def inject_status_function():
    """
    Inject the get_host_status function to the context.
    HTML templates can use this function to get the status of the host.
    """
    return dict(get_host_status=get_host_status)


#
# Routes
#


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


@host.route("/<int:host_id>/reset", methods=["POST"])
@login_required
@admin_required
def reset_host(host_id):
    """
    Reset the host statistics.
    """
    host = Host.query.get_or_404(host_id)
    host.reset_stats()
    db.session.commit()

    return redirect(url_for("host.index"))


@host.route("/<int:host_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_host(host_id):
    """
    Delete the host.
    """
    host = Host.query.get_or_404(host_id)
    if host.assigned_match_id:
        flash(f"The host {host.name} is currently assigned to a match. Unassign the host first.", "danger")
        return redirect(url_for("host.index"))

    db.session.delete(host)
    db.session.commit()

    return redirect(url_for("host.index"))
