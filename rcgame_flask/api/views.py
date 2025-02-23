import os
import re
import secrets
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import IntegrityError
from rcgame_flask.app import db, csrf
from rcgame_flask.auth.decorators import api_key_required, admin_api_key_required
from rcgame_flask.group.models import Group, GroupStats, Match, MatchStatus
from rcgame_flask.group.utils import save_group_metadata
from rcgame_flask.host.models import Host
from rcgame_flask.team.models import Team

api = Blueprint("api", __name__, url_prefix="/api")

#
# Client API
#


@api.route("/request_match", methods=["POST"])
@csrf.exempt
@api_key_required
def request_match():
    """
    Request a match.
    """
    data = request.get_json()
    host_name = data.get("host_name")
    start_time = datetime.now().replace(microsecond=0)

    if host_name is None:
        current_app.logger.error("Missing host name.")
        return jsonify({"error": "Missing host name."}), 400

    # Create or update the host record
    host = Host.query.filter_by(name=host_name).first()
    if host is None:
        host = Host(name=host_name)
        current_app.logger.info(f"@{host_name} Adding host {host_name} ...")
        db.session.add(host)

    client_ip = request.remote_addr
    # In case of reverse proxy
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(',')[0].strip()

    host.ip_v4_address = client_ip
    host.last_accessed_at = start_time
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    if host.assigned_match_id is not None:
        current_app.logger.warning(f"@{host_name} Already assigned a match.")
        return jsonify({"error": "Already assigned a match."}), 200

    # Find an unexecuted match
    match = Match.query.filter_by(processed=MatchStatus.UNEXECUTED).first()
    if match is None:
        return jsonify({"message": "No scheduled matches."}), 200

    if match.group is None:
        return jsonify({"error": "Group found."}), 404
    if match.left_team is None:
        return jsonify({"error": "Left team not found."}), 404
    if match.right_team is None:
        return jsonify({"error": "Right team not found."}), 404

    # Assign the match to the host
    match.host_id = host.id
    match.host_name = host_name
    match.start_time = start_time
    match.processed = MatchStatus.IN_PROGRESS
    match.log_file_name = f"{str(match.index).zfill(5)}-{match.left_team.name}-{match.right_team.name}-{host_name}"
    match.token = secrets.token_hex(16)
    host.assigned_match_id = match.id
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    synch_mode = match.left_team.synch_mode and match.right_team.synch_mode

    current_app.logger.info(f"@{host_name} Assigned {match.group.name}/{match.index}")
    return jsonify(
        {
            "match_id": match.id,
            "group_id": match.group_id,
            "group_name": match.group.name,
            "index": match.index,
            "host_id": match.host_id,
            "host_name": match.host_name,
            "start_time": start_time,
            "left_team_name": match.left_team.name,
            "left_team_version": match.left_team.version,
            "right_team_name": match.right_team.name,
            "right_team_version": match.right_team.version,
            "log_file_name": match.log_file_name,
            "token": match.token,
            "synch_mode": synch_mode,
        }
    )


def extract_result_params(data):
    """
    Extract match result parameters.
    """
    try:
        return {
            "match_id": int(data.get("match_id")),
            "host_id": int(data.get("host_id")),
            "left_team_name": data.get("left_team_name"),
            "right_team_name": data.get("right_team_name"),
            "left_score": int(data.get("left_score")),
            "right_score": int(data.get("right_score")),
            "token": data.get("token"),
        }
    except Exception as e:
        raise ValueError(f"Invalid parameters: {e}")


def validate_match(match, params):
    """
    Validate the match and the parameters.
    """
    if match is None:
        return "Match not found.", 404
    if match.left_team is None or match.right_team is None:
        return "Teams not found.", 404
    if match.left_team.name != params["left_team_name"]:
        return "Left team name do not match.", 400
    if match.right_team.name != params["right_team_name"]:
        return "Right team name do not match.", 400
    if match.processed != MatchStatus.IN_PROGRESS:
        return "Match is not in progress.", 400
    if match.host_id != params["host_id"]:
        current_app.logger.error(f"@{match.host_name} Host ID does not match for {match.group.name}/{match.index}.")
        match.reset_assignment()
        db.session.commit()
        return "Host ID do not match.", 401
    if match.token != params["token"]:
        current_app.logger.error(f"@{match.host_name} Token does not match for {match.group.name}/{match.index}.")
        match.reset_assignment()
        db.session.commit()
        return "Token do not match.", 401
    if params["left_score"] < 0 or params["right_score"] < 0:
        current_app.logger.error(f"@{match.host_name} Invalid score for {match.group.name}/{match.index}.")
        match.reset_assignment()
        db.session.commit()
        return "Invalid score.", 400
    return None, 200


def save_log_files(match, group):
    """
    Save the log files.
    """
    log_dir = os.path.join(current_app.static_folder, "logs", group.name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    common_name = match.log_file_name
    count = 0
    for file in request.files.getlist("log_file"):
        if file and file.filename:
            new_file_name = re.sub(r'^[^.]+', common_name, file.filename)
            file.save(os.path.join(log_dir, new_file_name))
            count += 1
    current_app.logger.info(f"@{match.host_name} Saved    {group.name}/{match.index}, files={count}")


def update_match_result(match, params, end_time):
    """
    Update the match result.
    """
    match.end_time = end_time
    match.left_score = params["left_score"]
    match.right_score = params["right_score"]
    match.processed = MatchStatus.COMPLETED


def update_host(host, match, end_time):
    """
    Update the host record.
    """
    host.last_accessed_at = end_time
    host.assigned_match_id = None

    # The seconds of the match duration are calculated as the difference between the start and end times.
    duration = (end_time - match.start_time).total_seconds()
    if match.left_team.synch_mode and match.right_team.synch_mode:
        host.total_runtime_synch_mode += duration
        host.total_matches_synch_mode += 1
    else:
        host.total_runtime_normal += duration
        host.total_matches_normal += 1


@api.route("/submit_result", methods=["POST"])
@csrf.exempt
@api_key_required
def submit_result():
    """
    Submit a match result.
    """
    data = request.form.to_dict()
    try:
        params = extract_result_params(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    match = Match.query.get(params["match_id"])
    error_msg, status_code = validate_match(match, params)
    if error_msg:
        return jsonify({"error": error_msg}), status_code

    group = Group.query.get(match.group_id)
    if group is None:
        return jsonify({"error": "Group not found."}), 404

    # Save the log files and commit the result
    save_log_files(match, group)
    end_time = datetime.now().replace(microsecond=0)
    group.updated_at = end_time
    update_match_result(match, params, end_time)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    # Update the host record
    host = Host.query.get(match.host_id)
    if host is None:
        current_app.logger.error(f"@{match.host_name} Host not found.")
        return jsonify({"error": "Host not found."}), 404

    update_host(host, match, end_time)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    message = f"@{match.host_name} Result   {group.name}/{match.index}, {params['left_score']} - {params['right_score']}"
    current_app.logger.info(message)
    return jsonify({"message": message})


@api.route("/decline_match", methods=["POST"])
@csrf.exempt
@api_key_required
def decline_match():
    """
    Decline an assigned match.
    """
    data = request.form.to_dict()

    try:
        host_name = data.get("host_name")
        match_id = data.get("match_id")
        token = data.get("token")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    host = Host.query.filter_by(name=host_name).first()
    if host:
        host.last_accessed_at = datetime.now().replace(microsecond=0)
        host.assigned_match_id = None
        host.decline_count += 1
        db.session.commit()

    match = Match.query.get(match_id)
    if match is None:
        current_app.logger.error(f"@{host_name} deline_assignment: Match {match_id} not found.")
        return jsonify({"error": "Match not found."}), 404

    if match.token != token:
        current_app.logger.error(f"@{host_name} deline_assignment: Token does not match {match.group.name}/{match.index} @{match.host_name}")
        return jsonify({"error": "Token does not match."}), 401

    current_app.logger.info(f"@{match.host_name} Declined {match.group.name}/{match.index}")
    match.reset_assignment()
    db.session.commit()
    return jsonify({"message": "Match declined."})


@api.route("/download/<string:name>/<string:version>", methods=["GET"])
@api_key_required
def download(name, version):
    """
    Download the team archive.
    """
    client_ip = request.remote_addr
    # In case of reverse proxy
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(',')[0].strip()

    team = Team.query.filter_by(name=name, version=version).first()
    if team:
        print(team.archive_path)
        abs_path = os.path.join(current_app.static_folder, team.archive_path)
        try:
            current_app.logger.info(f"Send team {name} ({version}) to {client_ip}")
            return send_file(abs_path, as_attachment=True)
        except FileNotFoundError:
            abort(404)
        # The folloing code causes a problem for transferring a gzipped file.
        # return redirect(url_for("static", filename=team.archive_path))

    return jsonify({"error": "Team not found."}), 404


#
# Admin API
#


@api.route("/admin/create_group", methods=["POST"])
@csrf.exempt
@admin_api_key_required
def admin_api_create_group():
    """
    Create a group.
    """
    data = request.get_json()

    try:
        group_name = data.get("group_name")
        left_team_name = data.get("left_team_name")
        left_team_version = data.get("left_team_version")
        right_team_name = data.get("right_team_name")
        right_team_version = data.get("right_team_version")
        number_of_matches = data.get("number_of_matches")
        description = data.get("description") or ""
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if left_team_name is None or right_team_name is None:
        return jsonify({"error": "Missing team names."}), 400

    if left_team_version is None or right_team_version is None:
        return jsonify({"error": "Missing team versions."}), 400   

    if number_of_matches is None or number_of_matches <= 0:
        return jsonify({"error": "Invalid number of matches."}), 400

    left_team = Team.query.filter_by(name=left_team_name, version=left_team_version).first()
    if left_team is None:
        if left_team_version == "":
            team = Team(name=left_team_name, version="", archive_path="", is_active=False)
            db.session.add(team)
            db.session.commit()
            left_team = team
        else:
            return jsonify({"error": "Left team not found."}), 404

    right_team = Team.query.filter_by(name=right_team_name, version=right_team_version).first()
    if right_team is None:
        if right_team_version == "":
            team = Team(name=right_team_name, version="", archive_path="", is_active=False)
            db.session.add(team)
            db.session.commit()
            right_team = team
        else:
            return jsonify({"error": "Right team not found."}), 404

    now = datetime.now().replace(microsecond=0)
    # group_name = create_group_name(now, left_team, right_team)

    group = Group(
        name=group_name,
        created_at=now,
        left_team_id=left_team.id,
        right_team_id=right_team.id,
        description=description,
    )
    db.session.add(group)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": f"Group [{group_name}] cannot be created."}), 400

    group_stats = GroupStats(group.id)
    db.session.add(group_stats)
    db.session.commit()

    for i in range(number_of_matches):
        match = Match(
            index=i + 1,
            group_id=group.id,
            left_team_id=left_team.id,
            right_team_id=right_team.id,
            processed=MatchStatus.IN_PROGRESS,
        )
        db.session.add(match)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": f"Failed to create matches for group [{group_name}]."}), 400

    save_group_metadata(group)

    current_app.logger.info(f"Created {group.name} matches={number_of_matches}")
    return jsonify({"message": "Group created successfully.",
                    "group_id": group.id,
                    "group_name": group.name,
                    "number_of_matches": number_of_matches})


@api.route("/admin/submit_result", methods=["POST"])
@csrf.exempt
@admin_api_key_required
def admin_api_submit_result():
    """
    Submit a match result.
    """
    data = request.form.to_dict()
    # print("(submit_result) match_result:", data)
    # print("(submit_result) files:", request.files)

    try:
        group_id = data.get("group_id")
        host_name = data.get("host_name")
        left_team_name = data.get("left_team_name")
        right_team_name = data.get("right_team_name")
        left_team_version = data.get("left_team_version")
        right_team_version = data.get("right_team_version")
        left_score = data.get("left_score")
        right_score = data.get("right_score")
        log_file_name = data.get("log_file_name")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    start_time = datetime.now().replace(microsecond=0)
    end_time = start_time

    group = Group.query.filter_by(id=group_id).first()
    if group is None:
        return jsonify({"error": "Group not found."}), 404

    left_team = Team.query.filter_by(name=left_team_name, version=left_team_version).first()
    if left_team is None:
        return jsonify({"error": "Left team not found."}), 404

    right_team = Team.query.filter_by(name=right_team_name, version=right_team_version).first()
    if right_team is None:
        return jsonify({"error": "Right team not found."}), 404

    match = Match.query.filter(
        Match.group_id == group.id,
        Match.left_team_id == left_team.id,
        Match.right_team_id == right_team.id,
        Match.processed != MatchStatus.COMPLETED
    ).first()

    if match is None:
        return jsonify({"error": f"No uncompleted match in the group {group.name}"}), 404

    # Create the log directory
    log_dir = os.path.join(current_app.static_folder, "logs", group.name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Save the log files
    common_name = log_file_name
    count = 0
    for file in request.files.getlist("log_file"):
        if file and file.filename:
            new_file_name = re.sub(r'^[^.]+', common_name, file.filename)
            # print(f"Saving log file as {group.name}/{new_file_name}")
            file.save(os.path.join(log_dir, new_file_name))
            count += 1
    current_app.logger.info(f"@admin Saved {group.name}/{match.index} logs={count}")

    # Update the match record
    match.host_name = host_name
    match.start_time = start_time
    match.end_time = end_time
    match.left_score = left_score
    match.right_score = right_score
    match.log_file_name = log_file_name
    match.processed = MatchStatus.COMPLETED

    group.updated_at = end_time
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    host = Host.query.filter_by(name=host_name).first()
    if host is None:
        host = Host(name=host_name)
        print(f"Adding host {host.name} ...")
        db.session.add(host)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    current_app.logger.info(f"@admin Accepted {group.name}/{match.index}")
    return jsonify({"message": f"Accepted the result of match index={match.index}."})
