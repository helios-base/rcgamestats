import os
import csv
import io
import glob
from datetime import datetime
from flask import render_template, redirect, url_for, flash, jsonify, request, current_app
from flask import send_file, send_from_directory
from flask_login import login_required, current_user
from ..app import db
from . import group as group_bp
from .models import Group, Match, GroupStats
from .stats import plot_confidence_intervals
from ..config import config


@group_bp.route("/")
@login_required
def index():
    """
    Show active groups.
    """
    # group_list = Group.query.all()
    group_list = Group.query.filter_by(is_active=True).all()
    group_list.sort(key=lambda x: x.created_at, reverse=True)
    # for group in group_list:
    #     print(f"Group: {group.name}, {group.created_at}, {group.left_team}, {group.right_team}")
    return render_template("group/index.html", groups=group_list)


@group_bp.route("/stats/")
@login_required
def show_stats():
    """
    Show stats of all groups.
    """
    group_list = Group.query.filter_by(is_active=True).all()
    group_list.sort(key=lambda x: x.created_at, reverse=True)
    group_stats_list = []
    for group in group_list:
        stats = group.stats
        if stats is None:
            stats = GroupStats(group.id)
            db.session.add(stats)
            db.session.commit()
        if stats.updated_at is None or group.updated_at > stats.updated_at:
            stats.update()
            current_app.logger.info(f'Group {group.name} stats updated at {stats.updated_at}')

        group_stats_list.append(group.to_simple_json())

    db.session.commit()
    return render_template("group/stats.html", group_stats_list=group_stats_list)


@group_bp.route("/stats/updates", methods=["GET"])
@login_required
def get_updated_stats():
    """
    Ajax request.
    Returns updated stats of all groups since the last load.
    """
    last_load = request.args.get("last_load")
    if not last_load:
        return jsonify({"error": "last_load parameter is required"}), 400

    try:
        if last_load.isdigit():
            timestamp = int(last_load) / 1000.0
            last_load_dt = datetime.fromtimestamp(timestamp)
        else:
            last_load_dt = datetime.strptime(last_load, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    groups = Group.query.filter(Group.is_active == True, Group.updated_at > last_load_dt).all()
    group_stats_list = []
    for group in groups:
        stats = group.stats
        if stats is None:
            stats = GroupStats(group.id)
            stats.update()
            current_app.logger.info(f'Group {group.name} stats created at {stats.updated_at}')
            db.session.add(stats)
            db.session.commit()
        if stats.updated_at is None or group.updated_at > stats.updated_at:
            stats.update()
            current_app.logger.info(f'Group {group.name} stats updated at {stats.updated_at}')
            db.session.commit()
        group_stats_list.append(group.to_simple_json())

    return jsonify(group_stats_list=group_stats_list)


@group_bp.route("/archived/")
@login_required
def show_archived_groups():
    """
    Show all archived groups.
    """
    group_list = Group.query.filter_by(is_active=False).all()
    group_list.sort(key=lambda x: x.created_at, reverse=True)
    return render_template("group/archived_groups.html", groups=group_list)


# @group_bp.route("/all", methods=["GET"])
# @login_required
# def show_all_matches():
#     """
#     Show all matches.
#     """
#     matches = Match.query.all()
#     stats_list = GroupStats.query.all()
#     return render_template("group/all_matches.html", matches=matches, stats_list=stats_list)


@group_bp.route("/<string:group_name>/")
@login_required
def show_group_detail(group_name):
    """
    Show all matches associated with a group.
    """
    group = Group.query.filter_by(name=group_name).first()
    if group is None:
        flash(f"Group {group_name} not found.", "error")
        return redirect(url_for("group.index"))

    matches = Match.query.filter_by(group_id=group.id).all()

    use_googlesheet = False if (not current_user.is_admin
                                or config.GOOGLE_DOC_ID == ""
                                or config.GOOGLE_KEY_PATH == "") else True

    stats = group.stats
    if stats is None:
        stats = GroupStats(group.id)
        db.session.add(stats)
        db.session.commit()

    if stats.updated_at is None or group.updated_at > stats.updated_at:
        stats.update()
        current_app.logger.info(f'Group {group.name} stats updated at {stats.updated_at}')
        db.session.commit()

    return render_template(
        "group/detail.html",
        group=group,
        matches=matches,
        stats=stats,
        use_googlesheet=use_googlesheet
    )


@group_bp.route("/<int:group_id>/records", methods=["GET"])
@login_required
def get_match_records(group_id):
    """
    Ajax request.
    Get match table records for a group.
    """
    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 10, type=int)

    group = Group.query.get(group_id)
    if group is None:
        return jsonify({"error": "Group not found"}), 404

    matches = Match.query.filter_by(group_id=group_id).order_by(Match.index.asc()).offset(offset).limit(limit).all()
    match_records = []
    for match in matches:
        record = {
            "id": match.id,
            "index": match.index,
            "start_time": match.start_time.strftime("%Y-%m-%d %H:%M:%S") if match.start_time else "",
            "end_time": match.end_time.strftime("%Y-%m-%d %H:%M:%S") if match.end_time else "",
            "left_score": match.left_score,
            "right_score": match.right_score,
            "host_name": match.host_name if match.host_name else "",
            "host_id": match.host_id,
            "status": match.status.value,
            "log_url": url_for("group.show_match_log", group_name=group.name, index=match.index),
        }
        match_records.append(record)

    return jsonify(match_records=match_records)


@group_bp.route("/<string:group_name>/logs/", methods=["GET"])
@login_required
def show_group_logs(group_name):
    """
    Show log files for a group.
    """
    group = Group.query.filter_by(name=group_name).first()
    if group is None:
        flash(f"Group {group_name} not found.", "error")
        return redirect(url_for("group.index"))

    log_dir = os.path.join(current_app.static_folder, "logs", group_name)
    # if not os.path.exists(log_dir):
    #     flash(f"Log directory for group [{group_name}] not found.", "error")
    #     #return redirect(url_for("group.index"))
    #     return redirect(url_for("group.show_group_detail", group_name=group_name))

    matches_in_group = Match.query.filter_by(group_id=group.id).all()
    log_file_paths = []
    for match in matches_in_group:
        log_file_paths.extend(
            glob.glob(os.path.join(log_dir, f"{match.log_file_name}*"))
        )
    file_names = [os.path.basename(file_path) for file_path in log_file_paths]
    file_names.sort()

    return render_template(
        "group/log_files.html", group_name=group_name, file_names=file_names
    )


@group_bp.route("/<int:group_id>/export_csv", methods=["POST"])
@login_required
def export_csv(group_id):
    """
    Export group data to a CSV file.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group {group_id} not found.", "error")
        return redirect(url_for("group.index"))

    matches = Match.query.filter_by(group_id=group.id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Group Information"])
    writer.writerow(["Group Name", group.name])
    writer.writerow(["Created At", group.created_at.strftime("%Y-%m-%d %H:%M:%S") if group.created_at else ""])
    writer.writerow(["Updated At", group.updated_at.strftime("%Y-%m-%d %H:%M:%S") if group.updated_at else ""])
    writer.writerow(["Is Active", group.is_active])
    writer.writerow(["Left Team", group.left_team.name if group.left_team else ""])
    writer.writerow(["Left Version", f"{group.left_team.version}" if group.left_team else ""])
    writer.writerow(["Right Team", group.right_team.name if group.right_team else ""])
    writer.writerow(["Right Version", f"{group.right_team.version}" if group.right_team else ""])
    writer.writerow(["Description", group.description if group.description else ""])
    writer.writerow(["Total Matches", len(matches)])

    writer.writerow([])
    writer.writerow(["Match Information"])
    writer.writerow([
        "Index", "Start Time", "End Time", "Left Score", "Right Score", "Host Name", "Status", "Log File Name"
    ])

    for match in matches:
        writer.writerow([
            match.index,
            match.start_time.strftime("%Y-%m-%d %H:%M:%S") if match.start_time else "",
            match.end_time.strftime("%Y-%m-%d %H:%M:%S") if match.end_time else "",
            match.left_score,
            match.right_score,
            match.host_name if match.host_name else "",
            match.status.value,
            match.log_file_name if match.log_file_name else ""
        ])

    # Create a response object with the CSV data
    return current_app.response_class(
        response=output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={group.name}.csv"}
    )


@group_bp.route("/<string:group_name>/<int:index>/", methods=["GET"])
@login_required
def show_match_log(group_name, index):
    """
    Show log files for a match.
    """
    group = Group.query.filter_by(name=group_name).first()
    if group is None:
        return jsonify({"error": "Group not found"}), 404

    match = Match.query.filter_by(group_id=group.id, index=index).first()

    if match is None:
        return jsonify({"error": "Match not found"}), 404

    if match.log_file_name is None:
        return jsonify({"error": "Log file name not found"}), 404

    log_dir = os.path.join(current_app.static_folder, "logs", group_name)

    if not os.path.exists(log_dir):
        return jsonify({"error": "Log directory [{log_dir}] not found"}), 404

    # log_files = [f for f in os.listdir(this_log_dir_path) if log_file_name in f]
    log_file_paths = glob.glob(os.path.join(log_dir, f"{match.log_file_name}*"))
    if not log_file_paths:
        return jsonify({"error": "No matching log files found"}), 404
    file_names = [os.path.basename(file_path) for file_path in log_file_paths]
    file_names.sort()

    return render_template(
        "group/log_files.html", group_name=group_name, file_names=file_names
    )


@group_bp.route("/<string:group_name>/logs/<path:file_name>", methods=["GET"])
@login_required
def download_log(group_name, file_name):
    """
    Download a log file.
    """
    log_dir = os.path.join(current_app.static_folder, "logs", group_name)
    try:
        response = send_from_directory(log_dir, file_name, as_attachment=True)
        response.headers["Content-Encoding"] = "identity"
        return response
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404


@group_bp.route("/plot_confidence_intervals", methods=["POST"])
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

    stats_list = []
    for group_id in group_ids:
        group = Group.query.get(group_id)
        if group is None:
            return jsonify({"error": f"Group ID {group_id} not found."}),
        stats = group.stats
        if stats is None:
            stats = GroupStats(group_id)
            db.session.add(stats)
            db.session.commit()
        if stats.updated_at is None or group.updated_at > stats.updated_at:
            stats.update()
            current_app.logger.info(f'Group {group.name} stats updated at {stats.updated_at}')
            db.session.commit()

        stats_list.append(stats)

    try:
        buf = plot_confidence_intervals(stats_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        # flash(f"Failed to plot stats: {str(e)}", "error")
        # return redirect(url_for("group.show_stats"))

    return send_file(buf, mimetype="image/png")


# @group_bp.route("/has_updates", methods=["GET"])
# @login_required
# def has_updates():
#     """
#     Check if there are any updates to the groups.
#     """
#     last_load_at = request.args.get("page_load_at")
#     # print(f"page_load_at: {last_load_at}")
#     # If last_load_at is None, return True as there are updates.
#     if last_load_at is None:
#         return jsonify({"update": True})

#     try:
#         if last_load_at.isdigit():
#             timestamp = int(last_load_at) / 1000.0
#             last_load_at_dt = datetime.fromtimestamp(timestamp)
#         else:
#             last_load_at_dt = datetime.strptime(last_load_at, "%Y-%m-%d %H:%M:%S")
#         # print(f"page_load_at: {last_load_at_dt}")
#     except ValueError:
#         return jsonify({"error": "Invalid datetime format"}), 400

#     group_list = Group.query.filter(Group.is_active == True, Group.updated_at > last_load_at_dt).all()
#     has_updates = len(group_list) > 0

#     # print(f"last_load_at_dt: {last_load_at_dt}")
#     # print(f"has_updates: {has_updates}")
#     return jsonify({"update": has_updates})
