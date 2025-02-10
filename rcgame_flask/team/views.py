import os
import shutil
from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask import send_file, abort
from flask_login import login_required
from werkzeug.utils import secure_filename
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
    Show all teams.
    """
    active_only = request.args.get('active_only', 'true').lower() == 'true'
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


@team.route("/<int:team_id>/delete", methods=["POST"])
@login_required
def delete(team_id):
    """
    Delete a team.
    """
    team = Team.query.get(team_id)
    if team:
        # Delete the archive file
        abs_path = os.path.join(current_app.static_folder, os.path.dirname(team.archive_path))
        if os.path.exists(abs_path):
            print(f"Delete {abs_path}")
            shutil.rmtree(abs_path)

    db.session.delete(team)
    db.session.commit()
    return redirect(url_for("team.index"))


@team.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """
    Upload team data.
    """
    form = TeamUploadForm()
    if form.validate_on_submit():
        # check if the team name and the version already exist
        team = Team.query.filter_by(name=form.team_name.data, version=form.version.data).first()
        if team:
            form.team_name.errors.append("team name and version already exist")
            return render_template("team/upload.html", form=form)

        name = secure_filename(form.team_name.data)
        version = secure_filename(form.version.data)
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
            name=form.team_name.data,
            version=form.version.data,
            synch_mode=form.synch_mode.data,
            archive_path=os.path.join(archive_dir, filename),
            description=form.description.data,
        )
        db.session.add(team)
        db.session.commit()
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
