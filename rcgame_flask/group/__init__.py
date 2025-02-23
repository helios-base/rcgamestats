from flask import Blueprint

group = Blueprint("group", __name__, template_folder="templates", url_prefix="/group")

from rcgame_flask.group import views_user, views_admin
