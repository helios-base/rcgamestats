import os
import requests
from config import config


def __create_diirectory(team_name, version):
    """
    Create the directory for the team with the given name and version.
    Args:
        team_name: The name of the team.
        version: The version of the team.
    Returns:
        The path to the team directory if it was successfully created, otherwise None.
    """
    # Create the team directory if it doesn't exist
    team_dir = os.path.join(config.TEAM_DIR, team_name, version)
    try:
        os.makedirs(team_dir)
    except FileExistsError:
        print(f"Team directory already exists: {team_dir}")
        return None
    except OSError:
        print(f"Failed to create team directory: {team_dir}")
        return None

    return team_dir


def __delete_directory(team_name, version):
    """
    Delete the directory for the team with the given name and version.
    Args:
        team_name: The name of the team.
        version: The version of the team.
    Returns:
        True if the directory was successfully deleted, otherwise False.
    """
    team_dir = os.path.join(config.TEAM_DIR, team_name, version)
    try:
        os.rmdir(team_dir)
        return True
    except FileNotFoundError:
        print(f"Team directory not found: {team_dir}")
        return False
    except OSError:
        print(f"Failed to delete team directory: {team_dir}")
        return False


def download_team(team_name, version):
    """
    Download the team with the given name and version from the server.
    Args:
        team_name: The name of the team.
        version: The version of the team.
    Returns:
        True if the team was successfully downloaded, otherwise False.
    """
    team_dir = __create_diirectory(team_name, version)
    if not team_dir:
        return False

    # Download the team from the server
    url = f"http://{config.SERVER_URL}/team/download/{team_name}/{version}"

    headers = {
        "x-api-key": config.API_KEY
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status() # Raise an exception for 4xx and 5xx status codes

    if response.status_code == 200:
        # Save the downloaded team to the team directory
        content_disposition = response.headers.get("Content-Disposition")
        if content_disposition:
            filename = content_disposition.split("filename=")[-1].strip('"')
        else:
            filename = f"{team_name}_{version}.tar.gz"

        team_file = os.path.join(team_dir, filename)
        with open(team_file, "wb") as file:
            file.write(response.content)

        print(f"Successfully downloaded team {team_name} version {version}.")
        return True
    else:
        print(f"Failed to download team {team_name} version {version}.")
        __delete_directory(team_name, version)
        return False
