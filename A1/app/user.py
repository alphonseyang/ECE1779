from flask import Blueprint

from app.login import login_required, login_admin_required

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route("/")
@login_required
@login_admin_required
def user_management():
    # TODO: show a list of user and can click to view user profile
    return "user management"


@bp.route("/<username>")
@login_required
def user_profile(username):
    # TODO retrieve the user information and render the user profile page
    return "user profile"


