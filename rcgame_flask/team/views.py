import os
import shutil
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask import send_file, abort, flash
from flask_login import login_required
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from rcgame_flask.app import db
from rcgame_flask.config import config
from rcgame_flask.auth.models import require_api_key
from rcgame_flask.team.forms import TeamUploadForm
from rcgame_flask.team.models import Team


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
def toggle_active(team_id):
    """
    Toggle active status of a team.
    """
    team = Team.query.get(team_id)
    team.is_active = not team.is_active
    db.session.commit()
    return redirect(url_for("team.index"))


@team.route("/<int:team_id>/delete", methods=["POST"])
@login_required
def delete(team_id):
    """
    Delete a team.
    """
    team = Team.query.get(team_id)
    if team:
        if team.is_active:
            flash(f"Team {team.name} ({team.version}) is active. Deactivate it first.")
            return redirect(url_for("team.index"))
        # Delete the archive file
        abs_path = os.path.join(current_app.static_folder, os.path.dirname(team.archive_path))
        if os.path.exists(abs_path):
            print(f"Delete {abs_path}")
            shutil.rmtree(abs_path)

    db.session.delete(team)
    db.session.commit()
    return redirect(url_for("team.index"))


@team.route("/bulk_archive", methods=["POST"])
@login_required
def bulk_archive():
    """
    Archive selected teams.
    """
    team_ids = request.form.getlist("team_ids")
    for team_id in team_ids:
        team = Team.query.get(team_id)
        if team is None:
            flash(f"Team {team_id} not found.")
            continue

        team.is_active = False
        db.session.commit()
        flash(f"Team {team.name} ({team.version}) archived.")

    return redirect(url_for("team.index"))


@team.route("/bulk_activate", methods=["POST"])
@login_required
def bulk_activate():
    """
    Activate selected teams.
    """
    team_ids = request.form.getlist("team_ids")
    for team_id in team_ids:
        team = Team.query.get(team_id)
        if team is None:
            flash(f"Team {team_id} not found.")
            continue

        if team.is_active:
            flash(f"Team {team.name} ({team.version}) is already active.")
            continue

        team.is_active = True
        db.session.commit()
        flash(f"Team {team.name} ({team.version}) activated.")

    return redirect(url_for("team.show_archived"))


@team.route("/bulk_delete_active", methods=["POST"])
@login_required
def bulk_delete():
    """
    Delete selected teams.
    """
    team_ids = request.form.getlist("team_ids")
    for team_id in team_ids:
        team = Team.query.get(team_id)
        if team is None:
            flash(f"Team {team_id} not found.")
            continue

        if team.is_active:
            flash(f"Team {team.name} ({team.version}) is active. Deactivate it first.")
            continue

        # Delete the archive file
        abs_path = os.path.join(current_app.static_folder, os.path.dirname(team.archive_path))
        if os.path.exists(abs_path):
            print(f"Delete {abs_path}")
            shutil.rmtree(abs_path)

        db.session.delete(team)
        db.session.commit()
        flash(f"Team {team.name} ({team.version}) deleted.")

    return redirect(url_for("team.show_archived"))


@team.route("/bulk_delete", methods=["POST"])
@login_required
def bulk_delete_teams():
    """
    Delete selected teams.
    """
    team_ids = request.form.getlist("team_ids")
    for team_id in team_ids:
        team = Team.query.get(team_id)
        if team is None:
            flash(f"Team {team_id} not found.")
            continue

        if team.is_active:
            flash(f"Team {team.name} ({team.version}) is active. Deactivate it first.")
            continue

        # Delete the archive file
        abs_path = os.path.join(current_app.static_folder, os.path.dirname(team.archive_path))
        if os.path.exists(abs_path):
            print(f"Delete {abs_path}")
            shutil.rmtree(abs_path)

        db.session.delete(team)
        db.session.commit()
        flash(f"Team {team.name} ({team.version}) deleted.")

    return redirect(url_for("team.show_archived"))


@team.route("/upload", methods=["GET", "POST"])
@login_required
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
            flash("team name is required")
            return render_template("team/upload.html", form=form), 400

        name = secure_filename(name)
        version = form.version.data if form.version.data else datetime.now().strftime("%Y%m%d-%H%M")
        version = secure_filename(version)

        print("upload", name, version) 
        # check if the team name and the version already exist
        team = Team.query.filter_by(name=name, version=version).first()
        if team is not None:
            form.team_name.errors.append("team name and version already exist")
            flash("team name and version already exist")
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
            flash("team name and version already exist")
            return render_template("team/upload.html", form=form)

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
        print(team.archive_path)
        abs_path = os.path.join(current_app.static_folder, team.archive_path)
        try:
            return send_file(abs_path, as_attachment=True)
        except FileNotFoundError:
            abort(404)
        # The folloing code causes a problem for transferring a gzipped file.
        # return redirect(url_for("static", filename=team.archive_path))

    return redirect(url_for("team.index"))


@team.route("/api_download/<string:name>/<string:version>", methods=["GET"])
@require_api_key
def api_download(name, version):
    """
    Download the team archive.
    """
    team = Team.query.filter_by(name=name, version=version).first()
    if team:
        print(team.archive_path)
        abs_path = os.path.join(current_app.static_folder, team.archive_path)
        try:
            return send_file(abs_path, as_attachment=True)
        except FileNotFoundError:
            abort(404)
        # The folloing code causes a problem for transferring a gzipped file.
        # return redirect(url_for("static", filename=team.archive_path))

    return redirect(url_for("team.index"))
