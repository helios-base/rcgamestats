import os
import json
from flask import current_app


def create_group_name(created_at, team_left, team_right):
    time_str = created_at.strftime('%Y%m%d-%H%M%S')
    return f"{time_str}-{team_left.name}-{team_right.name}"


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
