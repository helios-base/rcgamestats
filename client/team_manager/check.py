import os
import logging
from config import config    

logger = logging.getLogger("client")


def get_team_path(team_name, version):
    """
    Check if the team directory exists and contains a valid start script.
    Return the path to the start script if it exists, otherwise return None.
    Args:
        team_name: The name of the team.
        version: The version of the team.
    Returns:
        The path to the start script if it exists, otherwise None.
    """
    team_dir = os.path.join(config.TEAM_DIR, team_name, version)

    # Check if the team directory exists
    if not os.path.exists(team_dir) or not os.path.isdir(team_dir):
        logger.info(f"Team directory not found: {team_dir}")
        return None

    # Check if the team directory contains a directory
    # with an executable start script
    for entry in os.listdir(team_dir):
        entry_path = os.path.join(team_dir, entry)
        if os.path.isdir(entry_path):
            # Check if the directory contains 'start.sh'
            start_script = os.path.join(entry_path, "start.sh")
            if (
                os.path.exists(start_script)
                and os.path.isfile(start_script)
                and os.access(start_script, os.X_OK)
            ):
                return entry_path

    return None


def exist_team(team_name, version):
    """
    Check if the team start script exists.
    Args:
        team_name: The name of the team.
        version: The version of the team.
    Returns:
        True if the team start script exists, otherwise False.
    """
    return get_team_path(team_name, version) is not None
