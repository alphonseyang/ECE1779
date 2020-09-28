from flask import Blueprint

bp = Blueprint('login', __name__, url_prefix='/login')

@bp.route("/")
def login():
    return "a"
