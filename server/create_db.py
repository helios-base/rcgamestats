import os
import csv
import click
import secrets
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .app import db
from .auth.models import UserType, User, AllowedEmail, APIKey
from .team.models import Team
from .config import config


def __load_default_users(csv_path):
    users = []
    passwords = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        if set(reader.fieldnames) != set(["username", "email", "type"]):
            raise ValueError(f"Invalid header in {csv_path}")
        for line_num, row in enumerate(reader, start=1):
            username = row.get('username', '').strip()
            email = row.get('email', '').strip()
            type = row.get('type', '').strip()
            if not username or not email:
                print(f"Invalid user in {csv_path} line {line_num}")
                continue

            try:
                user_type = UserType(type)
            except ValueError:
                print(f"Invalid user type in {csv_path} line {line_num}")
                continue

            user = User(username=username, email=email, type=user_type)
            password = secrets.token_urlsafe(8)
            user.set_password(password)

            users.append(user)
            passwords.append(password)
    return users, passwords


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
    initial_password = config.ADMIN_PASSWORD if config.ADMIN_PASSWORD else secrets.token_urlsafe(8)

    admin = User(username=admin_username, type=UserType.MASTER)
    admin.email = admin_email
    admin.set_password(initial_password)
    db.session.add(admin)

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f'Error adding admin user: {e}')
        return
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f'Error adding admin user: {e}')
        return

    #
    # create default users
    #
    print("===== Adding default users =====")
    try:
        default_users_csv = os.path.join(base_dir, 'default_users.csv')
        users, passwords = __load_default_users(default_users_csv)
        for user, password in zip(users, passwords):
            print(f"Adding {user.username}, {user.email}, {user.type.value}, {password}")
            db.session.add(user)
    except ValueError as e:
        print(f'Error loading default users: {e}')

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f'Error adding default users: {e}')
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f'Error adding default users: {e}')

    #
    # create default allowed emails
    #
    print("")
    print("===== Adding default allowed emails =====")
    try:
        default_gmails_csv = os.path.join(base_dir, 'default_allowed_emails.csv')
        allowed_emails = __load_default_gmails(default_gmails_csv)
        for email in allowed_emails:
            print(f"Adding {email.email} as {email.type.value}")
            db.session.add(email)
    except ValueError as e:
        print(f'Error loading default allowed emails: {e}')

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f'Error adding default allowed emails: {e}')
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f'Error adding default allowed emails: {e}')

    #
    # register default teams
    #
    print("")
    print("===== Adding default teams =====")
    try:
        default_teams_csv = os.path.join(base_dir, 'default_teams.csv')
        teams = __load_default_teams(default_teams_csv)
        for team in teams:
            print(f"Adding {team.name}, {team.version}")
            db.session.add(team)
    except ValueError as e:
        print(f'Error loading default teams: {e}')

    try:
        db.session.commit()
    except IntegrityError as e:
        print(f'Error adding default allowed emails: {e}')
    except SQLAlchemyError as e:
        print(f'Error adding default allowed emails: {e}')

    #
    # create default API key for the admin user
    #
    default_key = config.ADMIN_API_KEY if config.ADMIN_API_KEY else secrets.token_urlsafe(16)
    default_api_key = APIKey(key=default_key, user_id=admin.id)
    db.session.add(default_api_key)
    try:
        db.session.commit()
    except IntegrityError as e:
        print(f'Error adding default API key: {e}')
    except SQLAlchemyError as e:
        print(f'Error adding default API key: {e}')

    print("")
    print("===== Initialization complete =====")
    print(f"Admin Username: {admin.username}")
    print(f"Admin Email: {admin.email}")
    print(f"Admin password: {initial_password}")
    print(f"Admin API key: {admin.api_keys.first().key}")
    print("")
    print("Please change the admin password and API key immediately.")
    print("")
    print("The default users, emails, and teams have been added.")
    print("Please review the default users and emails and remove any that are not needed.")
    print("The default teams have been added. Please review and update the teams as needed.")
    print("")
    print("The default users, emails, and teams are defined in the following files:")
    print(f"  {default_users_csv}")
    print(f"  {default_gmails_csv}")
    print(f"  {default_teams_csv}")
    print("")


@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    db.init_app(app)
    app.cli.add_command(init_db_command)
