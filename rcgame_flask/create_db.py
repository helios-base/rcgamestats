import os
import csv
import click
import secrets
from flask import current_app
from rcgame_flask.app import db
from rcgame_flask.auth.models import UserType, User, AllowedEmail, APIKey
from rcgame_flask.team.models import Team
from rcgame_flask.config import config


def __load_default_gmails(csv_path):
    allowed_emails = []
    required_headers = ["email", "type"]
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        if set(reader.fieldnames) != set(required_headers):
            raise ValueError(f"Invalid header in {csv_path}")
        for line_num, row in enumerate(reader, start=1):
            email = row.get('email', '').strip()
            type = row.get('type', '').strip()
            if not email or '@' not in email:
                print(f"Invalid email address in {csv_path} line {line_num}")
                continue
            try:
                user_type = UserType(type)
            except ValueError:
                print(f"Invalid user type in {csv_path} line {line_num}")
                continue
            allowed_emails.append(AllowedEmail(email=email, type=user_type))
    return allowed_emails


def __load_default_teams(csv_path):
    teams = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        if set(reader.fieldnames) != set(["name", "version", "synch_mode", "archive_path", "description"]):
            raise ValueError(f"Invalid header in {csv_path}")
        for line_num, row in enumerate(reader, start=1):
            name = row.get('name', '').strip()
            version = row.get('version', '').strip()
            synch_mode = row.get('synch_mode', '').strip()
            archive_path = row.get('archive_path', '').strip()
            description = row.get('description', '').strip()
            if not name or not version or not archive_path:
                print(f"Invalid team in {csv_path} line {line_num}")
                continue
            teams.append(Team(
                name=name,
                version=version,
                synch_mode=(synch_mode.lower() == "true"),
                archive_path=archive_path,
                description=description,
            ))
    return teams


def init_db():
    db.drop_all()
    db.create_all()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    #
    # create default admin user
    #
    if not config.ADMIN_USERNAME or not config.ADMIN_EMAIL:
        raise ValueError("ADMIN_USERNAME and ADMIN_EMAIL must be set in the config file.")

    admin_username = config.ADMIN_USERNAME
    admin_email = config.ADMIN_EMAIL
    initial_password = secrets.token_urlsafe(8)

    admin = User(username=admin_username, type=UserType.ADMIN)
    admin.email = admin_email
    admin.set_password(initial_password)
    db.session.add(admin)
    db.session.commit()

    #
    # create default allowed emails
    #
    try:
        default_gmails_csv = os.path.join(base_dir, 'default_allowed_emails.csv')
        allowed_emails = __load_default_gmails(default_gmails_csv)
        for email in allowed_emails:
            print(f"Adding {email.email} as {email.type.value}")
            db.session.add(email)
    except ValueError as e:
        print(f'Error loading default allowed emails: {e}')
    db.session.commit()

    #
    # register default teams
    #
    try:
        default_teams_csv = os.path.join(base_dir, 'default_teams.csv')
        teams = __load_default_teams(default_teams_csv)
        for team in teams:
            print(f"Adding {team.name}, {team.version}")
            db.session.add(team)
    except ValueError as e:
        print(f'Error loading default teams: {e}')
    db.session.commit()

    #
    # create default API key for the admin user
    #
    default_key = config.ADMIN_API_KEY if config.ADMIN_API_KEY else secrets.token_urlsafe(16)
    default_api_key = APIKey(key=default_key, user_id=admin.id)
    db.session.add(default_api_key)
    db.session.commit()

    print(f"Admin Username: {admin.username}")
    print(f"Admin Email: {admin.email}")
    print(f"Admin password: {initial_password}")
    print(f"Admin API key: {admin.api_keys.first().key}")


@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    db.init_app(app)
    app.cli.add_command(init_db_command)
