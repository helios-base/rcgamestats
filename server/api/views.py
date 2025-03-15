import os
import shutil
import re
import secrets
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask import send_file, abort
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from ..app import db, csrf
from ..auth.decorators import api_key_required, admin_api_key_required
from ..group.models import Group, GroupStats, Match, MatchStatus
from ..group.utils import save_group_metadata
from ..host.models import Host
from ..team.models import Team, current_datetime_str

api = Blueprint("api", __name__, url_prefix="/api")

#
# Client API
#


@api.route("/register_host", methods=["POST"])
@csrf.exempt
@api_key_required
def register_host():
    """
    Register a host.
    """
    data = request.get_json()
    host_id = data.get("host_id")
    host_name = data.get("host_name")
    host_token = data.get("host_token")

    if host_name is None:
        current_app.logger.error("Missing host name.")
        return jsonify({"error": "Missing host name."}), 400

    client_ip = request.remote_addr
    x_forwarded_for = request.headers.get('X-Forwarded-For')  # In case of reverse proxy
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(',')[0].strip()

    if host_id:
        host = Host.query.get(host_id)
        if host:
            if host_token:
                if host.token == host_token:
                    if host_name is not None and host.name != host_name:
                        host.name = host_name
                        current_app.logger.info(f"Updated host name: the name of host {host_id} is changed to {host_name}.")
                    host.last_accessed_at = datetime.now().replace(microsecond=0)
                    host.ip_v4_address = client_ip
                    db.session.commit()
                    return jsonify({"message": "Host already registered."})
                else:
                    current_app.logger.warning(f"Received invalid token for host id={host_id} name={host_name}.")
                    return jsonify({"error": "Invalid host token."}), 401
            else:
                current_app.logger.warning(f"Received a request to register an already registered host {host_name}.")
                return jsonify({"error": f"{host_name} already registererd. Please provide a token."}), 400
        # else:
        #     current_app.logger.warning(f"Host not found: id={host_id}.")
        #     return jsonify({"error": f"Host {host_id} not found."}), 404  

    # host not found, create a new host record
    host = Host(name=host_name, ip_v4_address=client_ip)
    db.session.add(host)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to register host {host_name}: {e}")
        return jsonify({"error": str(e)}), 500

    current_app.logger.info(f"Registered host: id={host.id} name={host_name}")
    return jsonify({"message": "Host registered.",
                    "host_id": host.id,
                    "host_token": host.token})


@api.route("/request_match", methods=["POST"])
@csrf.exempt
@api_key_required
def request_match():
    """
    Request a match.
    """
    data = request.get_json()
    host_id = data.get("host_id")
    host_name = data.get("host_name")
    host_token = data.get("host_token")
    start_time = datetime.now().replace(microsecond=0)

    if host_id is None:
        current_app.logger.error("Missing host ID.")
        return jsonify({"error": "Missing host ID."}), 400

    if host_name is None:
        current_app.logger.error("Missing host name.")
        return jsonify({"error": "Missing host name."}), 400

    if host_token is None:
        current_app.logger.error("Missing host token.")
        return jsonify({"error": "Missing host token."}), 400

    # Update the host record
    host = Host.query.get(host_id)
    if host is None:
        current_app.logger.error(f"Host {host_name} not found.")
        return jsonify({"error": "Host not found.",
                        "error_type": "host_not_found"}), 404
    if host.token != host_token:
        current_app.logger.error(f"Invalid token for host {host_name}.")
        return jsonify({"error": "Invalid token."}), 401

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
        match = Match.query.filter_by(id=host.assigned_match_id).first()
        if match and match.status == MatchStatus.IN_PROGRESS:
            current_app.logger.warning(f"@{host_name} Already assigned a match.")
            return jsonify({"error": "Already assigned a match."}), 200

    # Find an unexecuted match
    try:
        match = (
            Match.query
            .filter_by(status=MatchStatus.UNEXECUTED)
            .with_for_update(skip_locked=True)
            .first()
        )

        if match is None:
            return jsonify({"message": "No scheduled matches."}), 200
        if match.group is None:
            return jsonify({"error": "Group not found."}), 404
        if match.left_team is None:
            return jsonify({"error": "Left team not found."}), 404
        if match.right_team is None:
            return jsonify({"error": "Right team not found."}), 404

        # Assign the match to the host
        match.host_id = host.id
        match.host_name = host_name
        match.start_time = start_time
        match.status = MatchStatus.IN_PROGRESS
        match.log_file_name = f"{str(match.index).zfill(5)}-{match.left_team.name}-{match.right_team.name}-{host_name}"
        match.token = secrets.token_hex(16)
        host.assigned_match_id = match.id

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
            "match_token": match.token,
            "synch_mode": synch_mode,
        }
    )


#
# Helpers for submit_result
#


def extract_result_params(data):
    """
    Extract match result parameters.
    """
    try:
        return {
            "match_id": int(data.get("match_id")),
            "host_id": int(data.get("host_id")),
            "host_name": data.get("host_name"),
            "host_token": data.get("host_token"),
            "left_team_name": data.get("left_team_name"),
            "right_team_name": data.get("right_team_name"),
            "left_score": int(data.get("left_score")),
            "right_score": int(data.get("right_score")),
            "match_token": data.get("match_token"),
        }
    except Exception as e:
        raise ValueError(f"Invalid parameters: {e}")


def validate_host_token(host_id, host_name, host_token):
    """
    Validate the host token.
    """
    host = Host.query.get(host_id)
    if host is None:
        return "Invalid host id.", 401
    if host.name != host_name:
        return "Host name do not match.", 400
    if host.token != host_token:
        return "Token does not match,.", 401
    return None, 200


def validate_match(match, params):
    """
    Validate the match and the parameters.
    """
    if match is None:
        return "Match not found.", 404
    if match.group is None:
        return "Group not found.", 404
    if match.left_team is None or match.right_team is None:
        return "Teams not found.", 404
    if match.status != MatchStatus.IN_PROGRESS:
        return "Match is not in progress.", 410  # Gone
    if match.token != params["match_token"]:
        return "Token does not match.", 401  # Unauthorized
    if match.left_team.name != params["left_team_name"]:
        return "Left team name does not match.", 409  # Conflict
    if match.right_team.name != params["right_team_name"]:
        return "Right team name does not match.", 409  # Conflict
    if match.host_id != params["host_id"]:
        return "Host ID does not match.", 409  # Conflict
    if match.host is None:
        return "Host not found.", 404
    if params["left_score"] < 0 or params["right_score"] < 0:
        return "Invalid score.", 400  # Bad Request
    return None, 200


def save_log_files(match):
    """
    Save the log files.
    """
    log_dir = os.path.join(current_app.static_folder, "logs", match.group.name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    common_name = match.log_file_name
    count = 0
    for file in request.files.getlist("log_file"):
        if file and file.filename:
            new_file_name = re.sub(r'^[^.]+', common_name, file.filename)
            file.save(os.path.join(log_dir, new_file_name))
            count += 1
    current_app.logger.info(f"@{match.host_name} Saved    {match.group.name}/{match.index}, files={count}")


def update_match_result(match, params, end_time):
    """
    Update the match result.
    """
    match.end_time = end_time
    match.left_score = params["left_score"]
    match.right_score = params["right_score"]
    match.status = MatchStatus.COMPLETED


def update_host_by_submit(match, end_time):
    """
    Update the host record.
    """
    match.host.last_accessed_at = end_time
    match.host.assigned_match_id = None

    # The seconds of the match duration are calculated as the difference between the start and end times.
    duration = (end_time - match.start_time).total_seconds()
    if match.left_team.synch_mode and match.right_team.synch_mode:
        match.host.total_runtime_synch_mode += duration
        match.host.total_matches_synch_mode += 1
    else:
        match.host.total_runtime_normal += duration
        match.host.total_matches_normal += 1


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

    error_msg, status_code = validate_host_token(params["host_id"], params["host_name"], params["host_token"])
    if error_msg:
        current_app.logger.error(f"@{params['host_name']} {error_msg}.")
        return jsonify({"error": error_msg}), status_code

    match = Match.query.get(params["match_id"])
    error_msg, status_code = validate_match(match, params)
    if error_msg:
        current_app.logger.error(f"@{params['host_name']} {error_msg} for {match.group.name}/{match.index}.")
        return jsonify({"error": error_msg}), status_code

    # Save the log files
    save_log_files(match)
    end_time = datetime.now().replace(microsecond=0)

    # Update group updated_at
    match.group.updated_at = end_time

    # Update the match result
    update_match_result(match, params, end_time)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    # Update the host record
    update_host_by_submit(match, end_time)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    message = f"@{match.host_name} Result   {match.group.name}/{match.index}, {match.left_score} - {match.right_score}"
    current_app.logger.info(message)
    return jsonify({"message": message})


@api.route("/decline_match", methods=["POST"])
@csrf.exempt
@api_key_required
def decline_match():
    """
    Decline an assigned match.
    """
    data = request.get_json()

    host_id = data.get("host_id")
    host_name = data.get("host_name")
    host_token = data.get("host_token")
    match_id = data.get("match_id")
    match_token = data.get("match_token")

    if host_id is None or host_name is None or host_token is None or match_id is None or match_token is None:
        current_app.logger.error("Missing parameters.")
        return jsonify({"error": "Missing parameters."}), 400

    host = Host.query.get(host_id)
    if host is None:
        current_app.logger.error(f"@{host_name} Decline: host not found.")
        return jsonify({"error": "Invalid host token."}), 404
    if host.token != host_token:
        current_app.logger.error(f"@{host_name} Decline: Token does not match.")
        return jsonify({"error": "Token does not match."}), 401

    host.last_accessed_at = datetime.now().replace(microsecond=0)
    host.assigned_match_id = None
    host.decline_count += 1
    db.session.commit()

    match = Match.query.get(match_id)
    if match is None:
        current_app.logger.error(f"@{host_name} deline_assignment: Match {match_id} not found.")
        return jsonify({"error": "Match not found."}), 404

    if match.token != match_token:
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
        # print(team.archive_path)
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
def admin_create_group():
    """
    Create a group through the admin API.
    This method is mainly used for continuous evaluation during the team development phase.
    Asssume to use the latest version teams if the team version is not specified.
    """
    data = request.get_json()

    try:
        left_team_name = data.get("left_team_name")
        left_team_version = data.get("left_team_version")
        right_team_name = data.get("right_team_name")
        right_team_version = data.get("right_team_version")
        number_of_matches = data.get("number_of_matches")
        description = data.get("description") or ""
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    current_app.logger.info(f"Creating group left={left_team_name} ({left_team_version}) right={right_team_name} ({right_team_version}) matches={number_of_matches}")

    if left_team_name is None or right_team_name is None:
        current_app.logger.error("Missing team names.")
        return jsonify({"error": "Missing team names."}), 400

    if left_team_version is None or right_team_version is None:
        current_app.logger.error("Missing team versions.")
        return jsonify({"error": "Missing team versions."}), 400

    if number_of_matches is None or number_of_matches <= 0:
        current_app.logger.error("Invalid number of matches.")
        return jsonify({"error": "Invalid number of matches."}), 400

    if number_of_matches > 10000:
        current_app.logger.error("Too many matches.")
        return jsonify({"error": f"Too many matches {number_of_matches}"}), 400

    if left_team_version == "":
        # If the version is not specified, use the latest version.
        left_team = Team.query.filter_by(name=left_team_name).order_by(Team.uploaded_at.desc()).first()
    else:
        left_team = Team.query.filter_by(name=left_team_name, version=left_team_version).first()
    if left_team is None:
        current_app.logger.error(f"Left team not found: {left_team_name} ({left_team_version})")
        return jsonify({"error": f"Left team not found. {left_team_name} ({left_team_version})"}), 404

    if right_team_version == "":
        # If the version is not specified, use the latest version.
        right_team = Team.query.filter_by(name=right_team_name).order_by(Team.uploaded_at.desc()).first()
    else:
        right_team = Team.query.filter_by(name=right_team_name, version=right_team_version).first()
    if right_team is None:
        current_app.logger.error(f"Right team not found: {right_team_name} ({right_team_version})")
        return jsonify({"error": f"Right team not found. {right_team_name} ({right_team_version})"}), 404

    now = datetime.now().replace(microsecond=0)

    from ..group.utils import create_group_name, save_group_metadata
    group_name = create_group_name(now, left_team, right_team)

    group = Group(
        name=group_name,
        created_at=now,
        updated_at=now,
        left_team_id=left_team.id,
        right_team_id=right_team.id,
        description=description,
    )
    db.session.add(group)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        current_app.logger.error(f"Group [{group_name}] cannot be created.")
        return jsonify({"error": f"Group [{group_name}] cannot be created."}), 400

    group_stats = GroupStats(group.id)
    db.session.add(group_stats)
    db.session.commit()

    for i in range(number_of_matches):
        match = Match(
            index=i + 1,
            group_id=group.id,
            left_team_id=left_team.id,
            right_team_id=right_team.id
        )
        db.session.add(match)
    db.session.commit()

    save_group_metadata(group)

    current_app.logger.info(f"Created {group.name} matches={number_of_matches} through admin API.")
    return jsonify({"message": "Group created successfully.",
                    "group_id": group.id,
                    "group_name": group.name,
                    "number_of_matches": number_of_matches})


@api.route("/admin/submit_group", methods=["POST"])
@csrf.exempt
@admin_api_key_required
def admin_submit_group():
    """
    Create a group from the existing log files.
    Not to assume that the new matches are executed.
    Instead, the log files are uploaded by the admin.
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

    if number_of_matches > 10000:
        return jsonify({"error": "Too many matches."}), 400

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
            status=MatchStatus.IN_PROGRESS,
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
def admin_submit_result():
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
        Match.status != MatchStatus.COMPLETED
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
    match.status = MatchStatus.COMPLETED

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


@api.route("/admin/upload_team", methods=["POST"])
@csrf.exempt
@admin_api_key_required
def admin_upload_team():
    """
    Upload a team archive.
    """
    team_name = request.form.get("team_name")
    team_version = request.form.get("team_version")
    synch_mode = request.form.get("synch_mode")
    description = request.form.get("description")
    if team_name is None:
        current_app.logger.error("admin_upload_team: Missing team name.")
        return jsonify({"error": "Missing team name."}), 400

    if team_version is None or team_version == "":
        team_version = current_datetime_str()

    team_name = secure_filename(team_name)
    team_version = secure_filename(team_version)

    if synch_mode is not None:
        if synch_mode.lower() in ["false", "0"]:
            synch_mode = False
        elif synch_mode.lower() in ["true", "1"]:
            synch_mode = True
        else:
            current_app.logger.error("admin_upload_team: Invalid synch_mode.")
            return jsonify({"error": "Invalid synch_mode."}), 400
    else:
        synch_mode = True

    if description is None:
        description = ""

    # Check if the team already exists
    team = Team.query.filter_by(name=team_name, version=team_version).first()
    if team is not None:
        current_app.logger.error("admin_upload_team: Team already exists.")
        return jsonify({"error": "Team already exists."}), 400

    archive_dir = os.path.join("teams", team_name, team_version)
    absolute_path = os.path.join(current_app.static_folder, archive_dir)
    if not os.path.exists(absolute_path):
        os.makedirs(absolute_path)

    # Save the uploaded file
    files = request.files.getlist("team_archive")
    if len(files) == 0:
        current_app.logger.error("admin_upload_team: No file uploaded.")
        return jsonify({"error": "No file uploaded."}), 400
    if len(files) > 1:
        current_app.logger.error("admin_upload_team: Multiple files uploaded.")
        return jsonify({"error": "Multiple files uploaded."}), 400
    file = files[0]
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(absolute_path, filename))
    else:
        current_app.logger.error("admin_upload_team: No file uploaded.")
        return jsonify({"error": "No file uploaded."}), 400

    # Create a new team record
    team = Team(name=team_name,
                version=team_version,
                synch_mode=synch_mode,
                archive_path=os.path.join(archive_dir, filename),
                description=description)
    db.session.add(team)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        shutil.rmtree(absolute_path)
        return jsonify({"error": str(e)}), 500

    current_app.logger.info(f"admin_upload_team: Uploaded team {team_name} ({team_version})")
    return jsonify({"message": "Team uploaded successfully."})
