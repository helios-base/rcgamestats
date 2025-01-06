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