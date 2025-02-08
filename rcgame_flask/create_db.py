from flask import current_app
from rcgame_flask.app import db
from rcgame_flask.auth.models import User, APIKey
from rcgame_flask.team.models import Team
import csv
import click
import secrets


def init_db():
    db.drop_all()
    db.create_all()

    initial_password = secrets.token_urlsafe(8)
    admin = User(username="admin", type="admin")
    admin.set_password(initial_password)
    db.session.add(admin)

    # teamlist.csvのデータを挿入
    with current_app.open_resource("teamlist.csv") as f:
        reader = csv.reader(f.read().decode("utf8").splitlines())
        for row in reader:
            if len(row) == 3:
                team = Team(
                    name=row[0],
                    synch_mode=(row[1].strip().lower() == "true"),
                    archive_path=row[2],
                )
                db.session.add(team)

    default_api_key = APIKey(key="xchuqnjxcnauhnjnxpzsjdiwjksa")
    db.session.add(default_api_key)

    db.session.commit()

    print(f"Admin user created with password: {initial_password}")

@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    db.init_app(app)
    app.cli.add_command(init_db_command)
