from flask import Blueprint

from app.login import login_worker

bp = Blueprint('login', __name__, url_prefix='/login')


@bp.route('/', methods=('GET', 'POST'))
def login():
    return login_worker.work()
