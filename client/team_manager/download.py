import os
import requests
import tarfile
import zipfile
# import shutil
import logging
from urllib.parse import urljoin
from config import config

logger = logging.getLogger("client")


def __exist_directory(team_name, version):
    """
    Check if the directory for the team with the given name and version exists.
    Args:
        team_name: The name of the team.
        version: The version of the team.
    Returns:
        True if the directory exists, otherwise False.
    """
    team_dir = os.path.join(config.TEAM_DIR, team_name, version)
    return os.path.exists(team_dir) and os.path.isdir(team_dir)


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
        logger.error(f"Team directory already exists: {team_dir}")
        return None
    except OSError:
        logger.error(f"Failed to create team directory: {team_dir}")
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
        # os.rmdir(team_dir)
        #shutil.rmtree(team_dir)
        return True
    except FileNotFoundError:
        logger.error(f"Team directory not found: {team_dir}")
        return False
    except OSError:
        logger.error(f"Failed to delete team directory: {team_dir}")
        return False


def __extract_team(team_name, version, filename):
    """
    Extract the team with the given name and version from the downloaded archive.
    Args:
        team_name: The name of the team.
        version: The version of the team.
        team_file_path: The path to the downloaded team archive.
    Returns:
        True if the team was successfully extracted, otherwise False.
    """
    team_dir = os.path.join(config.TEAM_DIR, team_name, version)
    if not os.path.exists(team_dir) or not os.path.isdir(team_dir):
        logger.error(f"Team directory not found: {team_dir}")
        return False

    team_file_path = os.path.join(team_dir, filename)
    if not os.path.exists(team_file_path) or not os.path.isfile(team_file_path):
        logger.error(f"Team archive not found: {team_file_path}")
        return False

    try:
        if filename.endswith(".tar.gz") or filename.endswith(".tgz"):
            with tarfile.open(team_file_path, "r:gz") as tar:
                tar.extractall(path=team_dir)
        elif filename.endswith(".tar.bz2"):
            with tarfile.open(team_file_path, "r:bz2") as tar:
                tar.extractall(path=team_dir)
        elif filename.endswith(".tar.xz"):
            with tarfile.open(team_file_path, "r:xz") as tar:
                tar.extractall(path=team_dir)
        elif filename.endswith(".tar"):
            with tarfile.open(team_file_path, "r:") as tar:
                tar.extractall(path=team_dir)
        elif filename.endswith(".zip"):
            with zipfile.ZipFile(team_file_path, "r") as zip_ref:
                zip_ref.extractall(team_dir)
        else:
            logger.error(f"Unsupported archive format: {filename}")
            return False
    except (tarfile.TarError, zipfile.BadZipFile) as e:
        logger.error(f"Failed to extract team archive: {team_file_path}. Error: {e}")
        return False

    logger.info(f"Successfully extracted: {team_dir}/{filename}")
    return True


def download_team(team_name, version):
    """
    Download the team with the given name and version from the server.
    Args:
        team_name: The name of the team.
        version: The version of the team.
    Returns:
        True if the team was successfully downloaded, otherwise False.
    """
    if __exist_directory(team_name, version):
        logger.error(f"Team directory already exists: {team_name} / {version}")
        return False

    team_dir = __create_diirectory(team_name, version)
    if not team_dir:
        return False

    # Download the team from the server
    endpoint = "api/download/{team_name}/{version}"
    url = urljoin(config.SERVER_URL, endpoint)

    headers = {
        "Accept-Encoding": "identity",
        "x-api-key": config.API_KEY
    }

    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes

    logger.info(f"Download status code: {response.status_code}")
    if response.status_code != 200:
        logger.error(f"Failed to download team {team_name} version {version}.")
        __delete_directory(team_name, version)
        return False

    # Save the downloaded team to the team directory
    content_disposition = response.headers.get("Content-Disposition")
    if content_disposition:
        filename = content_disposition.split("filename=")[-1].strip('"')
    else:
        filename = f"{team_name}_{version}.tar.gz"

    team_file_path = os.path.join(team_dir, filename)
    with open(team_file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    logger.info(f"Successfully downloaded: {team_file_path}")
    if not __extract_team(team_name, version, filename):
        __delete_directory(team_name, version)
        return False

    return True