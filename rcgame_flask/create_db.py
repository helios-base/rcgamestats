import csv
import click
import secrets
from flask import current_app
from rcgame_flask.app import db
from rcgame_flask.auth.models import User, APIKey
from rcgame_flask.team.models import Team
from rcgame_flask.config import config


def init_db():
    db.drop_all()
    db.create_all()

    # create admin user
    admin_username = config.ADMIN_USERNAME if config.ADMIN_USERNAME else "admin"
    admin_email = config.ADMIN_EMAIL if config.ADMIN_EMAIL else "example@example.com"
    initial_password = secrets.token_urlsafe(8)
    admin_api_key = config.ADMIN_API_KEY if config.ADMIN_API_KEY else secrets.token_urlsafe(16)

    admin = User(username=admin_username, type="admin")
    admin.email = admin_email
    admin.set_password(initial_password)
    db.session.add(admin)
    db.session.commit()

    # teamlist.csvのデータを挿入
    with current_app.open_resource("teamlist.csv") as f:
        reader = csv.reader(f.read().decode("utf8").splitlines())
        for row in reader:
            if len(row) == 5:
                team = Team(
                    name=row[0],
                    version=row[1],
                    synch_mode=(row[2].strip().lower() == "true"),
                    archive_path=row[3],
                    description=row[4],
                )
                db.session.add(team)

    default_api_key = APIKey(key=admin_api_key, user_id=admin.id)
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
