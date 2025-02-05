import os
import shutil
from rcgame_flask.app import db
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required
from rcgame_flask.group.models import Group, Match
from rcgame_flask import googlesheet


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


@group.route("/<int:group_id>/delete", methods=["POST"])
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
@group.route("/<int:group_id>/reset/<int:match_id>", methods=["POST"])
@login_required
def reset_match(group_id, match_id):
    """
    Reset a match.
    """
    match = Match.query.filter_by(group_id=group_id, match_id=match_id).first()
    if match and match.processed == "in progress":
        match.host_name = None
        match.start_time = None
        match.processed = "unexecuted"
        db.session.commit()
        flash(f"Match {match.match_index} has been reset.")
    else:
        flash(f"Match not found or not in progress.")

    return redirect(url_for("group.show_group_matches", group_id=group_id))


@group.route("/<int:group_id>/logs", methods=["GET"])
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


@group.route("/<int:group_id>/log/<int:match_id>", methods=["GET"])
@login_required
def show_match_log(group_id, match_id):
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


@group.route("/<int:group_id>/upload", methods=["POST"])
@login_required
def upload_group_results_to_google_sheet(group_id):
    """
    Upload group results to Google Spreadsheet.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.")
        return redirect(url_for("group.index"))

    group_name = group.group_name
    if group_name is None:
        flash(f"Group ID {group_id} has no name.")
        return redirect(url_for("group.index"))

    group_time = group.group_time
    left_team = group.left_team
    right_team = group.right_team
    memo = group.group_memo

    print(f'(upload_group_results_to_google_sheet) group_name: {group_name}, time: {group_time}, left_team: {left_team}, right_team: {right_team}, memo: [{memo}]')

    # Get match records for the group
    match_records = Match.query.filter_by(group_id=group_id).all()

    # Upload group results to Google Spreadsheet
    if googlesheet.upload_group_results(group_name, group_time, left_team, right_team, memo, match_records):
        flash("Succeeded to upload the group results to the Google Spreadsheet.")
    else:
        flash("Failed to upload the group results to the Google Spreadsheet.")

    return redirect(url_for("group.show_group_matches", group_id=group_id))