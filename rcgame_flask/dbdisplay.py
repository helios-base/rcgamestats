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

@bp.route('/group_matches')
def show_group_matches():
    db = get_db()
    matches = db.execute('SELECT * FROM group_matches').fetchall()
    return render_template('dbdisplay/group_matches.html', matches=matches)

@bp.route('/matches')
def show_matches():
    db = get_db()
    matches = db.execute('SELECT * FROM matches').fetchall()
    return render_template('dbdisplay/matches.html', matches=matches)