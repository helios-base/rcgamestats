import os
import shutil
from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask import send_file, abort, flash
from flask_login import login_required
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from ..app import db
from ..auth.decorators import admin_required
from ..group.models import Group
from .forms import TeamUploadForm
from .models import Team, current_datetime_str


team = Blueprint("team", __name__, template_folder="templates", url_prefix="/team")


@team.route("/")
@login_required
def index():
    """
    Show active teams.
    """
    teams = Team.query.filter_by(is_active=True).all()

    return render_template("team/index.html", teams=teams)


@team.route("/archived")
@login_required
def show_archived():
    """
    Show archived teams.
    """
    teams = Team.query.filter_by(is_active=False).all()
    return render_template("team/archived.html", teams=teams)


@team.route("/<int:team_id>/toggle_active", methods=["POST"])
@login_required
@admin_required
def toggle_active(team_id):
    """
    Toggle active status of a team.
    """
    team = Team.query.get(team_id)
    if team is None:
        flash(f"Team {team_id} not found.", "error")
        return redirect(url_for("team.index"))
    if not team.is_active and team.version == "":
        flash(f"Team {team.name} has no version.", "error")
        current_app.logger.error(f"toggle_active: Team {team.name} has no version.")
        return redirect(url_for("team.index"))

    team.is_active = not team.is_active
    db.session.commit()

    flash(f"Team {team.name} ({team.version}) is {'activated' if team.is_active else 'archived'}.", "success")
    current_app.logger.info(f"Toggled {team.name} ({team.version}), is_active={team.is_active}")
    return redirect(url_for("team.index"))


@team.route("/<int:team_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_team(team_id):
    """
    Delete a team.
    """
    team = Team.query.get(team_id)
    if team:
        if team.is_active:
            flash(f"Team {team.name} ({team.version}) is active. Deactivate it first.", "error")
            current_app.logger.error(f"delete_team: Team {team.name} ({team.version}) is active.")
            return redirect(url_for("team.index"))

        if Group.query.filter((Group.left_team_id == team_id) | (Group.right_team_id == team_id)).count() > 0:
            flash(f"Team {team.name} ({team.version}) is used in a group. Delete the group first.", "error")
            current_app.logger.error(f"delete_team: Team {team.name} ({team.version}) is used in a group.")
            return redirect(url_for("team.index"))

        # Delete the archive file
        abs_path = os.path.join(current_app.static_folder, os.path.dirname(team.archive_path))
        if os.path.exists(abs_path):
            # print(f"Delete {abs_path}")
            current_app.logger.info(f"detele_team: Delete {abs_path}")
            shutil.rmtree(abs_path)

    db.session.delete(team)
    db.session.commit()

    message = f"Deleted {team.name} ({team.version})"
    flash(message, "success")
    current_app.logger.info(message)
    return redirect(url_for("team.index"))


@team.route("/archive_teams", methods=["POST"])
@login_required
@admin_required
def archive_teams():
    """
    Archive selected teams.
    """
    team_ids = request.form.getlist("team_ids")
    for team_id in team_ids:
        team = Team.query.get(team_id)
        if team is None:
            flash(f"Team {team_id} not found.", "error")
            current_app.logger.error(f"archive_teams: Team {team_id} not found.")
            continue

        team.is_active = False
        db.session.commit()
        flash(f"Team {team.name} ({team.version}) archived.", "success")
        current_app.logger.info(f"Archived {team.name} ({team.version})")

    return redirect(url_for("team.index"))


@team.route("/activate_teams", methods=["POST"])
@login_required
@admin_required
def activate_teams():
    """
    Activate selected teams.
    """
    team_ids = request.form.getlist("team_ids")
    for team_id in team_ids:
        team = Team.query.get(team_id)
        if team is None:
            flash(f"Team {team_id} not found.", "error")
            current_app.logger.error(f"activate_teams: Team {team_id} not found.")
            continue

        if team.version == "":
            flash(f"Team {team.name} has no version. Activation is not allowed.", "error")
            current_app.logger.error(f"activate_teams: Team {team.name} has no version.")
            continue

        if team.is_active:
            flash(f"Team {team.name} ({team.version}) is already active.", "error")
            current_app.logger.error(f"activate_teams: Team {team.name} ({team.version}) is already active.")
            continue

        team.is_active = True
        db.session.commit()
        flash(f"Team {team.name} ({team.version}) activated.", "success")
        current_app.logger.info(f"Activated {team.name} ({team.version})")

    return redirect(url_for("team.show_archived"))


@team.route("/delete_teams", methods=["POST"])
@login_required
@admin_required
def delete_teams():
    """
    Delete selected teams.
    """
    team_ids = request.form.getlist("team_ids")
    for team_id in team_ids:
        team = Team.query.get(team_id)
        if team is None:
            flash(f"Team {team_id} not found.", "error")
            current_app.logger.error(f"delete_teams: Team {team_id} not found.")
            continue

        if team.is_active:
            flash(f"Team {team.name} ({team.version}) is active. Deactivate it first.", "error")
            current_app.logger.error(f"delete_teams: Team {team.name} ({team.version}) is active.")
            continue

        if Group.query.filter((Group.left_team_id == team_id) | (Group.right_team_id == team_id)).count() > 0:
            flash(f"Team {team.name} ({team.version}) is used in a group. Delete the group first.", "error")
            current_app.logger.error(f"delete_teams: Team {team.name} ({team.version}) is used in a group.")
            return redirect(url_for("team.show_archived"))

        # Delete the archive file
        abs_path = os.path.join(current_app.static_folder, os.path.dirname(team.archive_path))
        if os.path.exists(abs_path):
            # print(f"Delete {abs_path}")
            shutil.rmtree(abs_path)
            current_app.logger.info(f"Deleted {abs_path}")

        db.session.delete(team)
        db.session.commit()
        flash(f"Deleted {team.name} ({team.version}).", "success")
        current_app.logger.info(f"Deleted {team.name} ({team.version})")

    return redirect(url_for("team.show_archived"))


@team.route("/upload", methods=["GET", "POST"])
@login_required
@admin_required
def upload():
    """
    Upload team data.
    """
    form = TeamUploadForm()

    ative_teams = Team.query.filter_by(is_active=True).all()
    teams_by_name = [""]
    for t in ative_teams:
        if t.name not in teams_by_name:
            teams_by_name.append(t.name)
    form.existing_team_name.choices = teams_by_name

    if form.validate_on_submit():
        name = form.new_team_name.data if form.new_team_name.data else form.existing_team_name.data
        if name == "":
            form.new_team_name.errors.append("team name is required")
            flash("team name is required", "error")
            current_app.logger.error("team/upload: team name is required")
            return render_template("team/upload.html", form=form), 400

        name = secure_filename(name)
        name = name.replace("-", "")
        version = form.version.data if form.version.data else current_datetime_str()
        version = secure_filename(version)

        # check if the team name and the version already exist
        team = Team.query.filter_by(name=name, version=version).first()
        if team is not None:
            form.team_name.errors.append("team name and version already exist")
            flash("team name and version already exist", "error")
            current_app.logger.error("team/upload: team name and version already exist")
            return render_template("team/upload.html", form=form), 409

        # Create a directory for the team with the name and version
        archive_dir = os.path.join("teams", name, version)
        absolute_path = os.path.join(current_app.static_folder, archive_dir)
        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)

        # Save the uploaded file
        file = form.archive_file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(absolute_path, filename))

        team = Team(
            name=name,
            version=version,
            synch_mode=form.synch_mode.data,
            archive_path=os.path.join(archive_dir, filename),
            description=form.description.data,
        )
        db.session.add(team)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.team_name.errors.append("team name and version already exist")
            message = f"team name {name} and version {version} already exist"
            flash(message, "error")
            current_app.logger.error(f"team/upload: {message}")
            return render_template("team/upload.html", form=form)

        flash(f"Team {name} ({version}) uploaded.", "success")
        current_app.logger.info(f"Uploaded {name} ({version})")
        return redirect(url_for("team.index"))

    return render_template("team/upload.html", form=form)


@team.route("/download/<string:name>/<string:version>", methods=["GET"])
@login_required
def download(name, version):
    """
    Download the team archive.
    """
    team = Team.query.filter_by(name=name, version=version).first()
    if team:
        abs_path = os.path.join(current_app.static_folder, team.archive_path)
        try:
            return send_file(abs_path, as_attachment=True)
        except FileNotFoundError:
            abort(404)
        # The folloing code causes a problem for transferring a gzipped file.
        # return redirect(url_for("static", filename=team.archive_path))

    return redirect(url_for("team.index"))
