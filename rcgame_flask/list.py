import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from rcgame_flask.db import get_db

bp = Blueprint('list', __name__)

@bp.route('/')
def index():
    return render_template('list/index.html')

@bp.route('/teams')
def show_teams():
    db = get_db()
    teams = db.execute('SELECT * FROM teams').fetchall()
    return render_template('list/teams.html', teams=teams)