import os
import shutil
from rcgame_flask.app import db
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, current_app
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


# TODO: POSTメソッドに変更する
@group.route("/reset/<int:match_id>", methods=["GET"])
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


@group.route("/group_logs/<int:group_id>", methods=["GET"])
@login_required
def show_group_logs(group_id):
    """
    Show log files for a group.
    """
    matches_in_group = Match.query.filter_by(group_id=group_id).all()
    log_files = []
    log_directory = None

    logs_dir = os.path.join(current_app.static_folder, "logs")
    for match in matches_in_group:
        if match.log_directory_name is not None:
            log_directory = match.log_directory_name
            this_log_dir_path = os.path.join(logs_dir, match.log_directory_name)
            if os.path.exists(this_log_dir_path):
                log_files.extend([f for f in os.listdir(this_log_dir_path) if match.log_file_name in f])

    return render_template("group/log_files.html", log_files=log_files, log_directory=log_directory)


@group.route("/match_log/<int:match_id>", methods=["GET"])
@login_required
def show_match_log(match_id):
    """
    Show log files for a match.
    """
    match = Match.query.get(match_id)

    if match is None:
        return jsonify({"error": "Match not found"}), 404

    if match.log_directory_name is None:
        return jsonify({"error": "Log directory not found"}), 404
    
    if match.log_file_name is None:
        return jsonify({"error": "Log file name not found"}), 404
    
    log_file_name = match.log_file_name
    logs_dir = os.path.join(current_app.static_folder, 'logs')

    this_log_dir_path = os.path.join(logs_dir, match.log_directory_name)

    if not os.path.exists(this_log_dir_path):
        return jsonify({"error": "Log directory not found"}), 404

    # TODO: more effiecient way to search for log files
    log_files = [f for f in os.listdir(this_log_dir_path) if log_file_name in f]

    if not log_files:
        return jsonify({"error": "No matching log files found"}), 404

    return render_template("group/log_files.html", log_files=log_files, log_directory=match.log_directory_name)
