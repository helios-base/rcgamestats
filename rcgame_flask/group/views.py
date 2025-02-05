import os
import shutil
from rcgame_flask.app import db
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from rcgame_flask.group.models import Group, Match


group = Blueprint("group", __name__, template_folder="templates", url_prefix="/group")


@group.route("/")
@login_required
def index():
    """
    Show all groups.
    """
    group_list = Group.query.all()
    return render_template("group/index.html", groups=group_list)


@group.route("/<int:group_id>")
@login_required
def show_group_matches(group_id):
    """
    Show all matches associated with a group.
    """
    matches = Match.query.filter_by(group_id=group_id).all()
    return render_template("group/match_list.html", group_id=group_id, matches=matches)


@group.route("/delete/<int:group_id>", methods=["POST"])
@login_required
def delete_group(group_id):
    """
    Delete a group and all matches associated with it.
    """
    matches_to_delete = Match.query.filter_by(group_id=group_id).all()
    group_to_delete = Group.query.get(group_id)

    logs_dir = os.path.join(current_app.static_folder, "logs")
    if matches_to_delete:
        for match in matches_to_delete:
            # delete the log directory
            if match.log_directory_name is not None:
                log_dir_path = os.path.join(logs_dir, match.log_directory_name)
                if os.path.exists(log_dir_path):
                    shutil.rmtree(log_dir_path)
            # delete the record
            db.session.delete(match)

    if group_to_delete:
        group_name = group_to_delete.group_name
        db.session.delete(group_to_delete)

    db.session.commit()
    flash(f"{group_name} has been deleted.")

    return redirect(url_for("group.index"))


@group.route("/reset_match/<int:match_id>", methods=["GET"])
@login_required
def reset_match(match_id):
    """
    Reset a match.
    """
    match = Match.query.get(match_id)
    if match and match.processed == "in progress":
        match.host_name = None
        match.start_time = None
        match.processed = "unexecuted"
        db.session.commit()

    return redirect(url_for("group.show_group_matches", group_id=match.group_id))
