import os
import shutil
import glob
import re
import secrets
from datetime import datetime
from rcgame_flask.app import db, csrf
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    request,
    current_app,
)
from flask_login import login_required
from rcgame_flask.auth.models import require_api_key
from rcgame_flask.group.models import Group, Match
from rcgame_flask.group.forms import GroupCreateForm
from rcgame_flask.team.models import Team
from rcgame_flask import googlesheet


group = Blueprint("group", __name__, template_folder="templates", url_prefix="/group")


#
# Group management
#


@group.route("/")
@login_required
def index():
    """
    Show all groups.
    """
    group_list = Group.query.all()
    group_list.sort(key=lambda x: x.created_at, reverse=True)
    return render_template("group/index.html", groups=group_list)


@group.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """
    Create a group.
    """
    form = GroupCreateForm()

    teams = Team.query.filter_by(is_active=True).all()
    form.team_left.choices = [(t.id, f"{t.name}:{t.version}") for t in teams]
    form.team_right.choices = [(t.id, f"{t.name}:{t.version}") for t in teams]

    if form.validate_on_submit():
        team_left_id = form.team_left.data
        team_right_id = form.team_right.data
        if form.team_left.data == form.team_right.data:
            flash("The same team cannot be selected for both sides.")
            return redirect(url_for("group.create"))

        team_left = Team.query.get(team_left_id)
        team_right = Team.query.get(team_right_id)
        if team_left is None:
            flash(f"Team ID {team_left_id} not found.")
            return redirect(url_for("group.create"))
        if team_right is None:
            flash(f"Team ID {team_right_id} not found.")
            return redirect(url_for("group.create"))

        now = datetime.now().replace(microsecond=0)
        group_name = (
            f"{now.strftime('%Y%m%d-%H%M%S')}-{team_left.name}-{team_right.name}"
        )

        group = Group(
            name=group_name,
            created_at=now,
            left_team_id=team_left_id,
            right_team_id=team_right_id,
            number_of_matches=form.number_of_matches.data,
            description=form.description.data,
        )
        db.session.add(group)
        db.session.commit()

        for i in range(int(form.number_of_matches.data)):
            match = Match(
                group_index=i + 1,
                group_id=group.id,
                left_team_id=team_left_id,
                right_team_id=team_right_id,
            )
            db.session.add(match)
        db.session.commit()

        flash(
            f"Created group {group_name} with {form.number_of_matches.data} matches for {team_left.name} vs. {team_right.name}."
        )
        return redirect(url_for("group.index"))

    return render_template("group/create.html", form=form)


@group.route("/<int:group_id>/")
@login_required
def show_group_matches_by_id(group_id):
    """
    Show all matches associated with a group.
    """
    group = Group.query.get_or_404(group_id)
    matches = Match.query.filter_by(group_id=group_id).all()
    return render_template(
        "group/match_list.html",
        group=group,
        matches=matches,
    )


@group.route("/<string:group_name>/")
@login_required
def show_group_matches(group_name):
    """
    Show all matches associated with a group.
    """
    group = Group.query.filter_by(name=group_name).first()
    if group is None:
        flash(f"Group {group_name} not found.")
        return redirect(url_for("group.index"))

    matches = Match.query.filter_by(group_id=group.id).all()
    return render_template(
        "group/match_list.html",
        group=group,
        matches=matches,
    )


@group.route("/<int:group_id>/logs/", methods=["GET"])
@login_required
def show_group_logs_by_id(group_id):
    """
    Show log files for a group.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.")
        return redirect(url_for("group.index"))

    dir_name = group.name
    log_dir = os.path.join(current_app.static_folder, "logs", dir_name)
    if not os.path.exists(log_dir):
        flash(f"Log directory for group [{group.name}] not found.")
        return redirect(url_for("group.index"))

    matches_in_group = Match.query.filter_by(group_id=group_id).all()
    log_file_paths = []
    for match in matches_in_group:
        log_file_paths.extend(
            glob.glob(os.path.join(log_dir, f"{match.log_file_name}*"))
        )
    file_names = [os.path.basename(file_path) for file_path in log_file_paths]
    file_names.sort()

    return render_template(
        "group/log_files.html", dir_name=dir_name, file_names=file_names
    )


@group.route("/<string:group_name>/logs/", methods=["GET"])
@login_required
def show_group_logs(group_name):
    """
    Show log files for a group.
    """
    group = Group.query.filter_by(name=group_name).first()
    if group is None:
        flash(f"Group {group_name} not found.")
        return redirect(url_for("group.index"))

    dir_name = group_name
    log_dir = os.path.join(current_app.static_folder, "logs", dir_name)
    if not os.path.exists(log_dir):
        flash(f"Log directory for group [{group_name}] not found.")
        return redirect(url_for("group.index"))

    matches_in_group = Match.query.filter_by(group_id=group.id).all()
    log_file_paths = []
    for match in matches_in_group:
        log_file_paths.extend(
            glob.glob(os.path.join(log_dir, f"{match.log_file_name}*"))
        )
    file_names = [os.path.basename(file_path) for file_path in log_file_paths]
    file_names.sort()

    return render_template(
        "group/log_files.html", dir_name=dir_name, file_names=file_names
    )


@group.route("/<int:group_id>/delete", methods=["POST"])
@login_required
def delete_group(group_id):
    """
    Delete a group and all matches associated with it.
    """
    group_to_delete = Group.query.get(group_id)
    if group_to_delete is None:
        flash(f"Group ID {group_id} not found.")
        return redirect(url_for("group.index"))

    log_dir = os.path.join(current_app.static_folder, "logs", group_to_delete.name)
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)

    matches_to_delete = Match.query.filter_by(group_id=group_id)
    matches_to_delete.delete(synchronize_session=False)

    group_name = group_to_delete.name
    db.session.delete(group_to_delete)
    db.session.commit()
    flash(f"The group [{group_name}] has been deleted.")

    return redirect(url_for("group.index"))


@group.route("/<int:group_id>/upload_to_google", methods=["POST"])
@login_required
def upload_group_results_to_google_sheet(group_id):
    """
    Upload group results to Google Spreadsheet.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.")
        return redirect(url_for("group.index"))

    group_name = group.name
    if group_name is None:
        flash(f"Group ID {group_id} has no name.")
        return redirect(url_for("group.index"))

    if group.left_team is None:
        flash(f"Group ID {group_id} has no left team.")
        return redirect(url_for("group.index"))
    if group.right_team is None:
        flash(f"Group ID {group_id} has no right team.")
        return redirect(url_for("group.index"))

    group_time = group.created_at
    left_team_name = group.left_team.name
    right_team_name = group.right_team.name
    description = group.description

    print(
        f"(upload_group_results_to_google_sheet) group_name: {group_name}, time: {group_time}, left_team: {left_team_name}, right_team: {right_team_name}, description: [{description}]"
    )

    # Get match records for the group
    match_records = Match.query.filter_by(group_id=group_id).all()

    # Upload group results to Google Spreadsheet
    if googlesheet.upload_group_results(
        group_name, group_time, left_team_name, right_team_name, description, match_records
    ):
        flash("Succeeded to upload the group results to the Google Spreadsheet.")
    else:
        flash("Failed to upload the group results to the Google Spreadsheet.")

    return redirect(url_for("group.show_group_matches", group_name=group.name))


#
# Match management
#


@group.route("/<int:group_id>/<int:match_id>/reset", methods=["POST"])
@login_required
def reset_match(group_id, match_id):
    """
    Reset a match.
    """
    match = Match.query.get(match_id)
    if match and match.processed == "in progress":
        match.host_name = None
        match.start_time = None
        match.processed = "unexecuted"
        match.log_file_name = None
        match.token = None
        db.session.commit()
        flash(f"Match {match.group_index} has been reset.")
    else:
        flash("Match not found or not in progress.")

    return redirect(url_for("group.show_group_matches_by_id", group_id=group_id))


@group.route("/<string:group_name>/<int:group_index>/log/", methods=["GET"])
@login_required
def show_match_log(group_name, group_index):
    """
    Show log files for a match.
    """
    group = Group.query.filter_by(name=group_name).first()
    if group is None:
        return jsonify({"error": "Group not found"}), 404

    match = Match.query.filter_by(group_id=group.id, group_index=group_index).first()

    if match is None:
        return jsonify({"error": "Match not found"}), 404

    if match.log_file_name is None:
        return jsonify({"error": "Log file name not found"}), 404

    dir_name = group_name
    log_dir = os.path.join(current_app.static_folder, "logs", dir_name)

    if not os.path.exists(log_dir):
        return jsonify({"error": "Log directory [{log_dir}] not found"}), 404

    # log_files = [f for f in os.listdir(this_log_dir_path) if log_file_name in f]
    log_file_paths = glob.glob(os.path.join(log_dir, f"{match.log_file_name}*"))
    if not log_file_paths:
        return jsonify({"error": "No matching log files found"}), 404
    file_names = [os.path.basename(file_path) for file_path in log_file_paths]
    file_names.sort()

    return render_template(
        "group/log_files.html", dir_name=dir_name, file_names=file_names
    )


#
# Client API
#


@group.route("/request_match", methods=["POST"])
@csrf.exempt
@require_api_key
def request_match():
    """
    Request a match.
    """
    data = request.get_json()
    host_name = data.get("host_name")

    if host_name is None:
        return jsonify({"error": "Missing host name."}), 400

    match = Match.query.filter_by(processed="unexecuted").first()
    if match is None:
        return jsonify({"message": "No unexecuted matches found."}), 200
    
    if match.group is None:
        return jsonify({"error": "Group name found."}), 404
    if match.left_team is None:
        return jsonify({"error": "Left team not found."}), 404
    if match.right_team is None:
        return jsonify({"error": "Right team not found."}), 404

    left_team_name = match.left_team.name
    left_team_version = match.left_team.version
    right_team_name = match.right_team.name
    right_team_version = match.right_team.version

    start_time = datetime.now().replace(microsecond=0)
    log_file_name = f"{str(match.group_index).zfill(5)}-{left_team_name}-{right_team_name}-{host_name}"

    match.host_name = host_name
    match.start_time = start_time
    match.processed = "in progress"
    match.log_file_name = log_file_name
    match.token = secrets.token_hex(16)

    db.session.commit()

    synch_mode = match.left_team.synch_mode and match.right_team.synch_mode

    return jsonify(
        {
            "match_id": match.id,
            "group_id": match.group_id,
            "group_name": match.group.name,
            "group_index": match.group_index,
            "host_name": match.host_name,
            "start_time": start_time,
            "left_team_name": left_team_name,
            "left_team_version": left_team_version,
            "right_team_name": right_team_name,
            "right_team_version": right_team_version,
            "log_file_name": log_file_name,
            "token": match.token,
            "synch_mode": synch_mode,
        }
    )


@group.route("/submit_result", methods=["POST"])
@csrf.exempt
@require_api_key
def submit_result():
    """
    Submit a match result.
    """
    print("(submit_result) request.form:", request.form)
    data = request.form.to_dict()
    print("(submit_result) match_result:", data)
    print("(submit_result) files:", request.files)

    try:
        match_id = data.get("match_id")
        left_team_name = data.get("left_team_name")
        right_team_name = data.get("right_team_name")
        left_score = data.get("left_score")
        right_score = data.get("right_score")
        token = data.get("token")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    end_time = datetime.now().replace(microsecond=0)

    match = Match.query.get(match_id)
    if match is None:
        return jsonify({"error": "Match not found."}), 404
    if match.left_team is None or match.right_team is None:
        return jsonify({"error": "Teams not found."}),
    if match.left_team.name != left_team_name:
        return jsonify({"error": "Left team name do not match."}), 400
    if match.right_team.name != right_team_name:
        return jsonify({"error": "Right team name do not match."}), 400

    print("(submit_result) found match data:", match.id, match.group_id, match.group.name, match.group_index)

    if match.token != token:
        return jsonify({"error": "Token does not match."}), 401

    group = Group.query.get(match.group_id)
    if group is None:
        return jsonify({"error": "Group not found."}), 404

    # Create the log directory
    log_dir = os.path.join(current_app.static_folder, "logs", group.name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Save the log files
    common_name = match.log_file_name
    for file in request.files.getlist("log_file"):
        if file and file.filename:
            #file.save(os.path.join(log_dir, file.filename))
            new_file_name = re.sub(r'^[^.]+', common_name, file.filename)
            print(f"Saving log file {file.filename} as {new_file_name} ...")
            file.save(os.path.join(log_dir, new_file_name))

    # Update the match record
    match.end_time = end_time
    match.left_score = left_score
    match.right_score = right_score
    match.processed = "completed"
    db.session.commit()

    return jsonify({"message": "Match result submitted."})


@group.route("/decline_assignment", methods=["POST"])
@csrf.exempt
@require_api_key
def decline_assignment():
    """
    Decline an assigned match.
    """
    data = request.form.to_dict()
    match_id = data.get("match_id")
    token = data.get("token")

    match = Match.query.get(match_id)
    if match is None:
        return jsonify({"error": "Match not found."}), 404

    if match.token != token:
        return jsonify({"error": "Token does not match."}), 401

    match.host_name = None
    match.start_time = None
    match.processed = "unexecuted"
    match.log_file_name = None
    match.token = None
    db.session.commit()

    return jsonify({"message": "Match declined."})
