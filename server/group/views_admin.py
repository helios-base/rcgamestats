import os
import glob
import shutil
from datetime import datetime
from flask import render_template, redirect, url_for, flash, current_app
from flask import request
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from ..app import db
from ..auth.decorators import admin_required
from ..team.models import Team
from .. import googlesheet
from . import group as group_bp
from .forms import GroupCreateForm, RoundrobinCreateForm
from .forms import GroupEditForm
from .models import Group, GroupStats, Match
from .utils import create_group_name, save_group_metadata
from .models import GroupStatus, MatchStatus


@group_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    """
    Create a group.
    """
    form = GroupCreateForm()

    teams = Team.query.filter_by(is_active=True).all()
    form.team_left.choices = [(t.id, f"{t.name}:{t.version}") for t in teams if t.version != ""]
    form.team_right.choices = [(t.id, f"{t.name}:{t.version}") for t in teams if t.version != ""]

    if form.validate_on_submit():
        team_left_id = form.team_left.data
        team_right_id = form.team_right.data
        if form.team_left.data == form.team_right.data:
            flash("The same team cannot be selected for both sides.", "error")
            current_app.logger.error("The same team cannot be selected for both sides.")
            return redirect(url_for("group.create"))

        team_left = Team.query.get(team_left_id)
        team_right = Team.query.get(team_right_id)
        if team_left is None:
            flash(f"Team ID {team_left_id} not found.", "error")
            current_app.logger.error(f"Team ID {team_left_id} not found.")
            return redirect(url_for("group.create"))
        if team_right is None:
            flash(f"Team ID {team_right_id} not found.", "error")
            current_app.logger.error(f"Team ID {team_right_id} not found.")
            return redirect(url_for("group.create"))

        now = datetime.now().replace(microsecond=0)
        group_name = create_group_name(now, team_left, team_right)

        group = Group(
            name=group_name,
            created_at=now,
            updated_at=now,
            left_team_id=team_left_id,
            right_team_id=team_right_id,
            description=form.description.data,
        )
        db.session.add(group)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"Group [{group_name}] cannot be created.", "error")
            current_app.logger.error(f"Group [{group_name}] cannot be created.")
            return redirect(url_for("group.create"))

        group_stats = GroupStats(group.id)
        db.session.add(group_stats)
        db.session.commit()

        for i in range(int(form.number_of_matches.data)):
            match = Match(
                index=i + 1,
                group_id=group.id,
                left_team_id=team_left_id,
                right_team_id=team_right_id,
            )
            db.session.add(match)
        db.session.commit()

        save_group_metadata(group)

        message = f"Created {group_name}, matches={form.number_of_matches.data}"
        flash(message, "success")
        current_app.logger.info(message)
        return redirect(url_for("group.index"))

    return render_template("group/create.html", form=form)


@group_bp.route("/create_roundrobin", methods=["GET", "POST"])
@login_required
@admin_required
def create_roundrobin():
    """
    Create round-robin groups.
    """
    form = RoundrobinCreateForm()

    teams = Team.query.filter_by(is_active=True).all()
    form.left_teams.choices = [(t.id, f"{t.name}:{t.version}") for t in teams if t.version != ""]
    form.right_teams.choices = [(t.id, f"{t.name}:{t.version}") for t in teams if t.version != ""]

    pairs_counts = {}
    if form.validate_on_submit():
        created_count = 0
        current_app.logger.info(f"Creating round-robin groups with {form.number_of_matches.data} matches each.")
        for left_id in form.left_teams.data:
            for right_id in form.right_teams.data:
                if left_id == right_id:
                    continue

                team_left = Team.query.get(left_id)
                team_right = Team.query.get(right_id)
                if team_left is None:
                    flash(f"Team ID {left_id} not found.", "error")
                    current_app.logger.error(f"Team ID {left_id} not found.")
                    return redirect(url_for("group.create_roundrobin"))
                if team_right is None:
                    flash(f"Team ID {right_id} not found.", "error")
                    current_app.logger.error(f"Team ID {right_id} not found.")
                    return redirect(url_for("group.create_roundrobin"))

                if team_left.name == team_right.name:
                    continue

                now = datetime.now().replace(microsecond=0)
                group_name = create_group_name(now, team_left, team_right)

                pairs_counts[(team_left.name, team_right.name)] = pairs_counts.get((team_left.name, team_right.name), 0) + 1
                if pairs_counts[(team_left.name, team_right.name)] > 1:
                    group_name = f"{group_name}_{pairs_counts[(team_left.name, team_right.name)]}"

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
                    flash(f"Group name [{group_name}] already exists.", "error")
                    current_app.logger.error(f"Group name [{group_name}] already exists.")
                    continue

                group_stats = GroupStats(group.id)
                db.session.add(group_stats)
                db.session.commit()

                for i in range(int(form.number_of_matches.data)):
                    match = Match(
                        index=i + 1,
                        group_id=group.id,
                        left_team_id=left_id,
                        right_team_id=right_id,
                    )
                    db.session.add(match)
                db.session.commit()

                save_group_metadata(group)
                created_count += 1
                current_app.logger.info(f"Created {group_name}, matches={form.number_of_matches.data}")

        message = f"Created {created_count} round-robin groups with {form.number_of_matches.data} matches each."
        flash(message, "success")
        current_app.logger.info(message)
        return redirect(url_for("group.index"))

    return render_template("group/create_roundrobin.html", form=form)


@group_bp.route("/<int:group_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_group(group_id):
    """
    Edit a group.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.", "error")
        current_app.logger.error(f"Group ID {group_id} not found.")
        return redirect(url_for("group.index"))

    form = GroupEditForm(obj=group)

    if form.validate_on_submit():
        number_of_matches = group.matches.count()
        if number_of_matches + form.additional_matches.data > 10000:
            flash("The total number of matches cannot exceed 10,000.", "error")
            current_app.logger.error("The total number of matches cannot exceed 10,000.")
            return redirect(url_for("group.edit_group", group_id=group_id))
        
        for i in range(int(form.additional_matches.data)):
            match = Match(
                index=number_of_matches + i + 1,
                group_id=group.id,
                left_team_id=group.left_team_id,
                right_team_id=group.right_team_id,
            )
            # print(f"Adding match {match.index} to group {group.name}")
            db.session.add(match)
        # print(f"Old description: {group.description}, New description: {form.description.data}")
        group.description = form.description.data
        db.session.commit()

        save_group_metadata(group)

        message = f"Updated {group.name}, +{form.additional_matches.data}"
        flash(message, "success")
        current_app.logger.info(message)

        if group.description != form.description.data:
            current_app.logger.info(f"Updated {group.name}, description edited")

        return redirect(url_for("group.index"))

    form.description.data = group.description

    return render_template("group/edit.html", form=form, group=group)


@group_bp.route("/<int:group_id>/archive", methods=["POST"])
@login_required
@admin_required
def archive_group(group_id):
    """
    Archive a group.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.", "error")
        current_app.logger.error(f"archive_group: Group ID {group_id} not found.")
        return redirect(url_for("group.index"))

    group.is_active = False

    matches_in_group = Match.query.filter_by(group_id=group_id).all()
    for match in matches_in_group:
        if match.status == MatchStatus.IN_PROGRESS or match.status == MatchStatus.UNEXECUTED:
            match.status = MatchStatus.ARCHIVED

    db.session.commit()

    flash(f"Group [{group.name}] has been archived.", "success")
    current_app.logger.info(f"Archived [{group.name}]")
    return redirect(url_for("group.index"))


def archive_groups(group_ids):
    """
    Bulk archive groups.
    """
    for group_id in group_ids:
        group = Group.query.get(group_id)
        if group is None:
            return "error", f"Group ID {group_id} not found."

        group.is_active = False

        matches_in_group = Match.query.filter_by(group_id=group_id).all()
        for match in matches_in_group:
            if match.status == MatchStatus.IN_PROGRESS or match.status == MatchStatus.UNEXECUTED:
                match.status = MatchStatus.ARCHIVED

        db.session.commit()
        current_app.logger.info(f"Archived {group.name}.")

    return "success", f"Archived {len(group_ids)} groups."


@group_bp.route("/bulk_action", methods=["POST"])
@login_required
@admin_required
def bulk_action():
    """
    Bulk action
    """
    action = request.form.get("action")
    group_ids = request.form.getlist("group_ids")
    if not group_ids:
        flash("No groups selected.", "error")
        return redirect(url_for("group.index"))

    result = "error"
    message = ""
    if action == "archive":
        result, message = archive_groups(group_ids)
    else:
        message = f"Unknown action [{action}]."

    flash(message, result)
    current_app.logger.info(message)
    return redirect(url_for("group.index"))


@group_bp.route("/unarchive_groups", methods=["POST"])
@login_required
@admin_required
def unarchive_groups():
    """
    Bulk unarchive groups.
    """
    group_ids = request.form.getlist('group_ids')
    if not group_ids:
        flash("No groups selected for unarchiving.", "error")
        current_app.logger.error("No groups selected for unarchiving.")
        return redirect(url_for("group.show_archived_groups"))

    for group_id in group_ids:
        group = Group.query.get(group_id)
        if group:
            group.is_active = True
            matches_in_group = Match.query.filter_by(group_id=group_id).all()
            for match in matches_in_group:
                if match.status == MatchStatus.ARCHIVED:
                    match.status = MatchStatus.UNEXECUTED
            current_app.logger.info(f"Unarchived {group.name}")

    db.session.commit()
    flash(f"Unarchived {len(group_ids)} groups.", "success")
    current_app.logger.info(f"Unarchived {len(group_ids)} groups")
    return redirect(url_for("group.show_archived_groups"))


@group_bp.route("/delete_groups", methods=["POST"])
@login_required
@admin_required
def delete_groups():
    """
    Bulk delete groups.
    """
    group_ids = request.form.getlist('group_ids')
    if not group_ids:
        flash("No groups selected for deletion.", "error")
        current_app.logger.error("No groups selected for deletion.")
        return redirect(url_for("group.show_archived_groups"))

    for group_id in group_ids:
        group = Group.query.get(group_id)
        if group:
            # matches = Match.query.filter_by(group_id=group_id)
            # if matches:
            #     matches.delete()

            # stats = GroupStats.query.filter_by(group_id=group_id)
            # if stats:
            #     stats.delete()

            db.session.delete(group)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(f"Group [{group.name}] cannot be deleted.", "error")
                continue

            log_dir = os.path.join(current_app.static_folder, "logs", group.name)
            if os.path.exists(log_dir):
                # print(f"Delete {log_dir}")
                shutil.rmtree(log_dir)
                current_app.logger.info(f"Deleted {log_dir}")

            current_app.logger.info(f"Deleted {group.name}")

    flash(f"Deleted {len(group_ids)} groups.", "success")
    current_app.logger.info(f"Deleted {len(group_ids)} groups")
    return redirect(url_for("group.show_archived_groups"))


@group_bp.route("/<int:group_id>/upload_to_google", methods=["POST"])
@login_required
@admin_required
def upload_group_results_to_google_sheet(group_id):
    """
    Upload group results to Google Spreadsheet.
    """
    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.", "error")
        return redirect(url_for("group.index"))

    group_name = group.name
    if group_name is None:
        flash(f"Group ID {group_id} has no name.", "error")
        return redirect(url_for("group.index"))

    if group.left_team is None:
        flash(f"Group ID {group_id} has no left team.", "error")
        return redirect(url_for("group.index"))
    if group.right_team is None:
        flash(f"Group ID {group_id} has no right team.", "error")
        return redirect(url_for("group.index"))

    group_time = group.created_at
    left_team_name = group.left_team.name
    right_team_name = group.right_team.name
    description = group.description

    flash(f"Uploading group results to Google Spreadsheet: group_name={group_name}", "success")
    current_app.logger.info(f"Uploading {group.name} to Google Spreadsheet.")

    # Get match records for the group
    match_records = Match.query.filter_by(group_id=group_id).all()

    # Upload group results to Google Spreadsheet
    if googlesheet.upload_group_results(
        group_name, group_time, left_team_name, right_team_name, description, match_records
    ):
        flash("Succeeded to upload the group results to the Google Spreadsheet.", "success")
        current_app.logger.info("Succeeded to upload the group results to the Google Spreadsheet.")
    else:
        flash("Failed to upload the group results to the Google Spreadsheet.", "error")
        current_app.logger.error("Failed to upload the group results to the Google Spreadsheet.")

    return redirect(url_for("group.show_group_detail", group_name=group.name))


#
# Match management
#


@group_bp.route("/<int:group_id>/reset_match/", methods=["POST"])
@login_required
@admin_required
def reset_match(group_id):
    """
    Reset a match.
    """
    match_id = request.form.get("match_id")
    if not match_id:
        flash("Match ID is missing.", "error")
        current_app.logger.error("reset_match: Match ID is missing.", "error")
        # return redirect(url_for("group.detail", group_id=request.args.get("group_id")))
        return redirect(url_for("group.detail", group_id=group_id))

    group = Group.query.get(group_id)
    if group is None:
        flash(f"Group ID {group_id} not found.", "error")
        current_app.logger.error(f"reset_match: Group ID {group_id} not found.")
        return redirect(url_for("group.index"))

    if group.is_active is False:
        flash(f"Group ID {group_id} is archived.", "error")
        current_app.logger.error(f"reset_match: Group ID {group_id} is archived.")
        return redirect(url_for("group.show_archived_groups"))

    match = Match.query.get(match_id)
    if match is None:
        flash(f"Match ID {match_id} not found.", "error")
        current_app.logger.error(f"reset_match: Match ID {match_id} not found.")
        return redirect(url_for("group.show_group_detail", group_name=group.name))

    group_name = match.group.name
    if match.status == MatchStatus.COMPLETED:
        if match.left_team.version == "" or match.right_team.version == "":
            flash("The match which has no team version cannot be reset.", "error")
            current_app.logger.error("reset_match: The match which has no team version cannot be reset.")
            return redirect(url_for("group.show_group_detail", group_name=group.name))

        log_dir = os.path.join(current_app.static_folder, "logs", match.group.name)
        log_file_paths = glob.glob(os.path.join(log_dir, f"{match.log_file_name}*"))
        for log_file_path in log_file_paths:
            # print(f"Removing log file {log_file_path} ...")
            current_app.logger.info(f"Removing log file {log_file_path} ...")
            os.remove(log_file_path)

        match.reset_assignment()
        group.updated_at = datetime.now().replace(microsecond=0)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"Match {group_name}/{match.index} cannot be reset.", "error")
            current_app.logger.error(f"Match {group_name}/{match.index} cannot be reset.")
            return redirect(url_for("group.show_group_detail", group_name=group_name))
        flash(f"Match {group_name}/{match.index} has been reset.", "success")
        current_app.logger.info(f"Reset {group_name}/{match.index}")
    elif match.status == MatchStatus.IN_PROGRESS:
        if match.host:
            match.host.assigned_match_id = None
            match.host.stats.reset_count += 1
            db.session.commit()

        match.reset_assignment()
        group.updated_at = datetime.now().replace(microsecond=0)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"Match {group_name}/{match.index} cannot be reset.", "error")
            current_app.logger.error(f"Match {group_name}/{match.index} cannot be reset.")
            return redirect(url_for("group.show_group_detail", group_name=group_name))
        flash(f"Match {group_name}/{match.index} has been reset.", "success")
        current_app.logger.info(f"Reset {group_name}/{match.index}")
    else:
        flash("Match not found or not in progress or completed.", "error")
        current_app.logger.error("reset_match: Match not found or not in progress or completed.", "error")

    return redirect(url_for("group.show_group_detail", group_name=group_name))
