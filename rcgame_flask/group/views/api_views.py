from datetime import datetime
from flask import jsonify, request)
from rcgame_flask.auth.decorators import api_key_required, admin_api_key_required

from ..views import group



#
# Admin API
#

@group.route("/api/create_group", methods=["POST"])
@csrf.exempt
@admin_api_key_required
def api_create_group():
    """
    Create a group.
    """
    data = request.get_json()

    left_team_name = data.get("left_team_name")
    left_team_version = data.get("left_team_version")
    right_team_name = data.get("right_team_name")
    right_team_version = data.get("right_team_version")
    number_of_matches = data.get("number_of_matches")
    description = data.get("description")

    if left_team_name is None or right_team_name is None:
        return jsonify({"error": "Missing team names."}), 400

    if left_team_version is None or right_team_version is None:
        return jsonify({"error": "Missing team versions."}), 400

    left_team = Team.query.filter_by(name=left_team_name, version=left_team_version).first()
    if left_team is None:
        return jsonify({"error": "Left team not found."}), 404

    right_team = Team.query.filter_by(name=right_team_name, version=right_team_version).first()
    if right_team is None:
        return jsonify({"error": "Right team not found."}), 404

    if number_of_matches is None or number_of_matches <= 0:
        return jsonify({"error": "Invalid number of matches."}), 400

    now = datetime.now().replace(microsecond=0)
    group_name = create_group_name(now, left_team, right_team)

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
        )
        db.session.add(match)
    db.session.commit()

    save_group_metadata(group)

    return jsonify({"message": f"Created group {group_name}."})
