from flask import Blueprint

from app.main import main_worker

bp = Blueprint('main', __name__)


@bp.route("/")
def main():
    return main_worker.work()
