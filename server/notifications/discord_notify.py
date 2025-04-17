import requests
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from ..app import db


def send_discord_notification(message):
    """
    Send a notification to a Discord channel using a webhook URL.
    :param webhook_url: The Discord webhook URL.
    :param message: The message to send.
    """
    webhook_url = current_app.config.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        # current_app.logger.error("Discord webhook URL is not set.")
        return

    data = {
        "content": message
    }

    print(f"Sending notification to Discord: {message}")
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        current_app.logger.info("Notification sent to Discord successfully.")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to send notification to Discord: {e}")
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred: {e}")


def notify_new_group(group):
    """
    Notify Discord about a new group creation.
    :param group: The group object containing group details.
    """
    with db.session.no_autoflush:
        match_count = group.matches.count()

    message = f"New group created: {group.name} with {match_count} matches."
    send_discord_notification(message)


def notify_group_all_completed(group):
    """
    Notify Discord about all tasks in a group being completed.
    :param group: The group object containing group details.
    """
    message = f"All matches for group {group.name} have been completed."
    send_discord_notification(message)
