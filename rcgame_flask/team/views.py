from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from rcgame_flask.app import db
from rcgame_flask.team.models import Team


team = Blueprint("team", __name__, template_folder="templates", url_prefix="/team")


@team.route("/")
@login_required
def index():
    """
    Show all teams.
    """
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    if active_only:
        teams = Team.query.filter_by(is_active=True).all()
    else:
        teams = Team.query.all()
    return render_template("team/index.html", teams=teams, active_only=active_only)


@team.route("/<int:team_id>/toggle_active", methods=["POST"])
@login_required
def toggle_active(team_id):
    """
    Toggle active status of a team.
    """
    team = Team.query.get(team_id)
    team.is_active = not team.is_active
    db.session.commit()
    return redirect(url_for("team.index"))
