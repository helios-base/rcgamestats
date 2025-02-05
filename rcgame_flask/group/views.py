from rcgame_flask.app import db
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from rcgame_flask.group.models import Group


group = Blueprint("group", __name__, template_folder="templates", url_prefix="/group")


@group.route("/")
@login_required
def index():
    group_list = Group.query.all()
    return render_template("group/index.html", groups=group_list)

