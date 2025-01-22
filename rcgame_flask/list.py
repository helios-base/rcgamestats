import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from rcgame_flask.auth import login_required
from rcgame_flask.models import db, teams
from flask_login import login_required
bp = Blueprint('list', __name__)

@bp.route('/')
@login_required
def index():
    team_list = teams.query.all()
    return render_template('list/index.html')
