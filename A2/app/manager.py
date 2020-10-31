"""
TODO: all manager related functionality is here, this is designed to be place to host
    all manager functionality, the tasks dispatched by main module will enter here、
"""
from threading import Lock

from flask import Blueprint, render_template

from app import constants

bp = Blueprint("manager", __name__, url_prefix="/")
# shared by main thread and auto-scaler thread to prevent race condition
lock = Lock()
workers_map = dict()
workers_num_history = [None] * 30


# TODO: create a starting worker when app is started and maybe other initialization
def app_initialization():
    # change_workers_num(True, 1)
    pass


# TODO: main page, need to call separate helper methods here
@bp.route("/")
def display_main_page():
    return render_template("main.html")


# TODO: query the AWS to show the number of worker over the past 30 minutes, or maybe use the auto-scaler to help you
#   track (it runs every minute), depends on your design
def workers_chart():
    pass


# TODO: list out the current workers with URLs and the DNS for AWS ELB
#   show the state of the instance (stopping and starting ones are considered working node)
#   need lock to view workers_map, and update worker_map if necessary (if stop/start is done, help update workers_map)
#   list the workers from the workers_map, not showing charts for pending state workers
def list_workers():
    pass


# TODO: up/down button invoked method, first check the workers then pass over to change_workers_num to finish
@bp.route("/change_workers", methods=["POST"])
def change_workers():
    # get the decision from the post form
    # use method verify_decision to ensure it is a valid decision
    # invoke change_workers_num to finish the work
    # notify if verify_decision return value is not the same as the passed in decision
    pass


# TODO: increase/decrease number of workers actual implementation
#   Yang idea: this should only be called by a method that wrapped in a lock, and the check
#   should be done before calling this method (caller should check in advance)
#   update the workers_map, ELB targets
def change_workers_num(is_increase: bool, changed_workers_num: int) -> bool:
    pass


# TODO: shut down all workers and the current manager app (close everything but keep data)
def terminate_manager():
    pass


# TODO: removed all application data including the images in S3 (not sure about the created users)
def remove_app_data():
    pass


# verify if the decision is valid and output a final decision
def verify_decision(decision):
    if (decision == constants.INCREASE_DECISION and len(workers_map) == constants.MAX_WORKER_NUM) \
            or (decision == constants.DECREASE_DECISION and len(workers_map) == constants.MIN_WORKER_NUM):
        decision = constants.MAINTAIN_DECISION
    return decision
