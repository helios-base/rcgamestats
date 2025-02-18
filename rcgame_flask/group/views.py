import os
import shutil
import glob
import re
import secrets
import json
from datetime import datetime
from rcgame_flask.app import db, csrf
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    flash,
    jsonify,
    request,
    current_app,
)
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from rcgame_flask.auth.models import require_api_key
from rcgame_flask.group.models import Group, Match, GroupStatus, MatchStatus
from rcgame_flask.group.forms import GroupCreateForm, GroupEditForm, RoundrobinCreateForm
from rcgame_flask.group.stats import GroupStats, plot_confidence_intervals
from rcgame_flask.team.models import Team
from rcgame_flask.config import config
from rcgame_flask import googlesheet


group = Blueprint("group", __name__, template_folder="templates", url_prefix="/group")


#
# Group management
#

def create_group_name(created_at, team_left, team_right, use_version=False):
    time_str = created_at.strftime('%Y%m%d-%H%M%S')
    if not use_version:
        return f"{time_str}-{team_left.name}-{team_right.name}"
    return f"{time_str}-{team_left.name}_{team_left.version}-{team_right.name}_{team_right.version}"


def save_group_metadata(group):
    metadata = {
        "name": group.name,
        "created_at": group.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "left_team": group.left_team.name,
        "left_team_version": group.left_team.version,
        "right_team": group.right_team.name,
        "right_team_version": group.right_team.version,
        "description": group.description,
        "scheduled_matches": group.matches.count(),
    }
    log_dir = os.path.join(current_app.static_folder, "logs", group.name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    metadata_file_path = os.path.join(log_dir, "group_info.json")
    with open(metadata_file_path, 'w') as metadata_file:
        json.dump(metadata, metadata_file, indent=4)


@group.route("/")
@login_required
def index():
    """
    Show active groups.
    """
    # group_list = Group.query.all()
    group_list = Group.query.filter_by(is_active=True).all()
    group_list.sort(key=lambda x: x.created_at, reverse=True)
    print(f"Group list: {group_list}")
    for group in group_list:
        print(f"Group: {group.name}, {group.created_at}, {group.left_team}, {group.right_team}")
    completed_counts = {group.id: Match.query.filter_by(group_id=group.id, processed=MatchStatus.COMPLETED).count() for group in group_list}
    return render_template("group/index.html", groups=group_list, completed_counts=completed_counts)


@group.route("/stats/")
@login_required
def show_stats():
    """
    Show stats of all groups.
    """
    group_list = Group.query.filter_by(is_active=True).all()
    group_list.sort(key=lambda x: x.created_at, reverse=True)
    stats_list = [GroupStats(group.id) for group in group_list]
    return render_template("group/stats.html", stats_list=stats_list)


@group.route("/archived/")
@login_required
def show_archived_groups():
    """
    Show all archived groups.
    """
    group_list = Group.query.filter_by(is_active=False).all()
    group_list.sort(key=lambda x: x.created_at, reverse=True)
    completed_counts = {group.id: Match.query.filter_by(group_id=group.id, processed=MatchStatus.COMPLETED).count() for group in group_list}
    return render_template("group/archived_groups.html", groups=group_list, completed_counts=completed_counts)


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
        group_name = create_group_name(now, team_left, team_right)

        group = Group(
            name=group_name,
            created_at=now,
            left_team_id=team_left_id,
            right_team_id=team_right_id,
            description=form.description.data,
        )
        db.session.add(group)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"Group [{group_name}] cannot be created.")
            return redirect(url_for("group.create"))

        save_group_metadata(group)

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


@group.route("/create_roundrobin", methods=["GET", "POST"])
@login_required
def create_roundrobin():
    """
    Create round-robin groups.
    """
    form = RoundrobinCreateForm()

    teams = Team.query.filter_by(is_active=True).all()
    form.left_teams.choices = [(t.id, f"{t.name}:{t.version}") for t in teams]
    form.right_teams.choices = [(t.id, f"{t.name}:{t.version}") for t in teams]

    if form.validate_on_submit():
        created_count = 0
        for left_id in form.left_teams.data:
            for right_id in form.right_teams.data:
                print(f"trying to create pair of left_id: {left_id}, right_id: {right_id}")
                if left_id == right_id:
                    continue

                team_left = Team.query.get(left_id)
                team_right = Team.query.get(right_id)
                if team_left is None:
                    flash(f"Team ID {left_id} not found.")
                    return redirect(url_for("group.create_roundrobin"))
                if team_right is None:
                    flash(f"Team ID {right_id} not found.")
                    return redirect(url_for("group.create_roundrobin"))

                if team_left.name == team_right.name:
                    continue

                now = datetime.now().replace(microsecond=0)
                group_name = create_group_name(now, team_left, team_right, use_version=True)

                group = Group(
                    name=group_name,
                    created_at=now,
                    left_team_id=left_id,
                    right_team_id=right_id,
                    description="",
                )
                db.session.add(group)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    flash(f"Group name [{group_name}] already exists.")
                    continue

                save_group_metadata(group)

                for i in range(int(form.number_of_matches.data)):
                    match = Match(
                        group_index=i + 1,
                        group_id=group.id,
                        left_team_id=left_id,
                        right_team_id=right_id,
                    )
                    db.session.add(match)
                db.session.commit()
                created_count += 1
        flash(f"Created {created_count} round-robin groups with {form.number_of_matches.data} matches each.")
        return redirect(url_for("group.index"))

    return render_template("group/create_roundrobin.html", form=form)


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

    use_googlesheet = False if config.GOOGLE_DOC_ID == "" or config.GOOGLE_KEY_PATH == "" else True

    stats = GroupStats(group.id)
    left_ci, right_ci = stats.compute_confidence_intervals()
    return render_template(
        "group/detail.html",
        group=group,
        matches=matches,
        stats=stats,
        left_score_confidence_interval=left_ci,
        right_score_confidence_interval=right_ci,
        use_googlesheet=use_googlesheet
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
    # if not os.path.exists(log_dir):
    #     flash(f"Log directory for group [{group_name}] not found.")
    #     #return redirect(url_for("group.index"))
    #     return redirect(url_for("group.show_group_matches", group_name=group_name))

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


@group.route("/<int:group_id>/edit", methods=["GET", "POST"])
@login_required
def edit_group(group_id):
    """
    Edit a group.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.", "error")
        return redirect(url_for("group.index"))

    form = GroupEditForm(obj=group)

    if form.validate_on_submit():
        number_of_matches = group.matches.count()
        for i in range(int(form.additional_matches.data)):
            match = Match(
                group_index=number_of_matches + i + 1,
                group_id=group.id,
                left_team_id=group.left_team_id,
                right_team_id=group.right_team_id,
            )
            print(f"Adding match {match.group_index} to group {group.name}")
            db.session.add(match)
        print(f"Old description: {group.description}, New description: {form.description.data}")
        group.description = form.description.data
        db.session.commit()

        save_group_metadata(group)

        flash(
            f"Updated group {group.name} with {form.additional_matches.data} matches."
        )
        return redirect(url_for("group.index"))

    form.description.data = group.description

    return render_template("group/edit.html", form=form, group=group)


@group.route("/<int:group_id>/archive", methods=["POST"])
@login_required
def archive_group(group_id):
    """
    Archive a group.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.")
        return redirect(url_for("group.index"))

    group.is_active = False

    matches_in_group = Match.query.filter_by(group_id=group_id).all()
    for match in matches_in_group:
        if match.processed == MatchStatus.IN_PROGRESS or match.processed == MatchStatus.UNEXECUTED:
            match.processed = MatchStatus.ARCHIVED

    db.session.commit()
    flash(f"Group [{group.name}] has been archived.")

    return redirect(url_for("group.index"))


@group.route("/bulk_action", methods=["POST"])
@login_required
def bulk_action():
    """
    Archive selected groups.
    """

    action = request.form.get("action")
    group_ids = request.form.getlist("group_ids")
    if not group_ids:
        flash("No groups selected.", "error")
        return redirect(url_for("group.index"))

    if action == "archive":
        return bulk_archive_groups(group_ids)
    elif action == "approve":
        return bulk_set_status_groups(group_ids, GroupStatus.APPROVED)
    elif action == "reject":
        return bulk_set_status_groups(group_ids, GroupStatus.REJECTED)
    elif action == "under_review":
        return bulk_set_status_groups(group_ids, GroupStatus.UNDER_REVIEW)
    elif action == "reset_status":
        return bulk_set_status_groups(group_ids, GroupStatus.NORMAL)

    flash(f"Unknown action [{action}].", "error")
    return redirect(url_for("group.index"))


def bulk_set_status_groups(group_ids, status):
    """
    Bulk approve groups.
    """
    for group_id in group_ids:
        group = Group.query.get(group_id)
        if group is None:
            flash(f"Group ID {group_id} not found.", "error")
            return redirect(url_for("group.index"))

        group.status = status
        db.session.commit()
        # flash(f"Group [{group.name}] has been set to [{status.value}].")

    return redirect(url_for("group.index"))


def bulk_archive_groups(group_ids):
    """
    Bulk archive groups.
    """
    for group_id in group_ids:
        group = Group.query.get(group_id)
        if group is None:
            flash(f"Group ID {group_id} not found.", "error")
            return redirect(url_for("group.index"))

        group.is_active = False

        matches_in_group = Match.query.filter_by(group_id=group_id).all()
        for match in matches_in_group:
            if match.processed == MatchStatus.IN_PROGRESS or match.processed == MatchStatus.UNEXECUTED:
                match.processed = MatchStatus.ARCHIVED

        db.session.commit()
        flash(f"Group [{group.name}] has been archived.")

    return redirect(url_for("group.index"))


@group.route("/bulk_unarchive_groups", methods=["POST"])
@login_required
def bulk_unarchive_groups():
    """
    Bulk unarchive groups.
    """
    group_ids = request.form.getlist('group_ids')
    if not group_ids:
        flash("No groups selected for unarchiving.")
        return redirect(url_for("group.show_archived_groups"))

    for group_id in group_ids:
        group = Group.query.get(group_id)
        if group:
            group.is_active = True
            matches_in_group = Match.query.filter_by(group_id=group_id).all()
            for match in matches_in_group:
                if match.processed == MatchStatus.ARCHIVED:
                    match.processed = MatchStatus.UNEXECUTED

    db.session.commit()
    flash(f"Unarchived {len(group_ids)} groups.")
    return redirect(url_for("group.show_archived_groups"))


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
    if matches_to_delete:
        matches_to_delete.delete()

    group_name = group_to_delete.name
    db.session.delete(group_to_delete)
    db.session.commit()
    flash(f"The group [{group_name}] has been deleted.")

    return redirect(url_for("group.index"))


@group.route("/bulk_delete_groups", methods=["POST"])
@login_required
def bulk_delete_groups():
    """
    Bulk delete groups.
    """
    group_ids = request.form.getlist('group_ids')
    if not group_ids:
        flash("No groups selected for deletion.")
        return redirect(url_for("group.show_archived_groups"))

    for group_id in group_ids:
        group = Group.query.get(group_id)
        if group:
            log_dir = os.path.join(current_app.static_folder, "logs", group.name)
            if os.path.exists(log_dir):
                print(f"Delete {log_dir}")
                shutil.rmtree(log_dir)
            matches = Match.query.filter_by(group_id=group_id)
            if matches:
                matches.delete()
                db.session.delete(group)

    db.session.commit()
    flash(f"Deleted {len(group_ids)} groups.")
    return redirect(url_for("group.show_archived_groups"))


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


@group.route("/reset_match", methods=["POST"])
@login_required
def reset_match():
    """
    Reset a match.
    """
    match_id = request.form.get("match_id")
    if not match_id:
        flash("Match ID is missing.", "error")
        return redirect(url_for("group.detail", group_id=request.args.get("group_id")))

    match = Match.query.get(match_id)
    if match is None:
        flash(f"Match ID {match_id} not found.")
        return redirect(url_for("group.show_group_matches", group_name=group.name))

    group_name = match.group.name
    if match.processed == MatchStatus.COMPLETED:
        log_dir = os.path.join(current_app.static_folder, "logs", match.group.name)
        log_file_paths = glob.glob(os.path.join(log_dir, f"{match.log_file_name}*"))
        for log_file_path in log_file_paths:
            print(f"Removing log file {log_file_path} ...")
            os.remove(log_file_path)

        match.host_name = None
        match.start_time = None
        match.end_time = None
        match.processed = MatchStatus.UNEXECUTED
        match.log_file_name = None
        match.token = None
        db.session.commit()
        flash(f"Match {match.group_index} has been reset.")
    elif match.processed == MatchStatus.IN_PROGRESS:
        match.host_name = None
        match.start_time = None
        match.processed = MatchStatus.UNEXECUTED
        match.log_file_name = None
        match.token = None
        db.session.commit()
        flash(f"Match {match.group_index} has been reset.")
    else:
        flash("Match not found or not in progress or completed.")

    return redirect(url_for("group.show_group_matches", group_name=group_name))


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


@group.route("/plot_confidence_intervals", methods=["POST"])
@login_required
def plot_groups_confidence_intervals():
    """
    Plot match results.
    """
    group_ids_raw = request.form.getlist("group_ids")
    if not group_ids_raw or len(group_ids_raw) == 0 or group_ids_raw[0] == "":
        return jsonify({"error": "No groups selected."}), 400

    group_ids = [int(id) for id in group_ids_raw[0].split(",")]
    group_ids.reverse()
    stats_list = [GroupStats(group_id) for group_id in group_ids]
    image_dir = os.path.join(current_app.static_folder, "images")
    try:
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        image_path = plot_confidence_intervals(image_dir, stats_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        # flash(f"Failed to plot stats: {str(e)}", "error")
        # return redirect(url_for("group.show_stats"))

    return send_file(image_path, mimetype="image/png")

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

    match = Match.query.filter_by(processed=MatchStatus.UNEXECUTED).first()
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
    match.processed = MatchStatus.IN_PROGRESS
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
    match.processed = MatchStatus.COMPLETED
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
    match.processed = MatchStatus.UNEXECUTED
    match.log_file_name = None
    match.token = None
    db.session.commit()

    return jsonify({"message": "Match declined."})
