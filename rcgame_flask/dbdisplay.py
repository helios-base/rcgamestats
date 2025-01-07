import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from rcgame_flask.db import get_db

bp = Blueprint('dbdisplay', __name__, url_prefix='/dbdisplay')

@bp.route('/teams')
def show_teams():
    db = get_db()
    teams = db.execute('SELECT * FROM teams').fetchall()
    return render_template('dbdisplay/teams.html', teams=teams)

@bp.route('/test_matche')
def show_match():
    db = get_db()
    match = db.execute('SELECT * FROM test_matche').fetchall()
    return render_template('dbdisplay/test_matche.html', match=match)