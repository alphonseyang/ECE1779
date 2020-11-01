"""
TODO: all manager related functionality is here, this is designed to be place to host
    all manager functionality, the tasks dispatched by main module will enter here、
"""
from threading import Lock

from flask import Blueprint, flash, render_template, redirect, request, url_for

from app import aws_helper, constants

bp = Blueprint("manager", __name__, url_prefix="/")
# shared by main thread and auto-scaler thread to prevent race condition
lock = Lock()
workers_map = dict()
workers_num_history = [None] * 30


# TODO: create a starting worker when app is started and maybe other initialization
#   this should not require lock as we know this is running alone during app creation
def app_initialization():
    # retrieve credentials first
    aws_helper.check_credentials_expire()
    change_workers_num(True, 1)
    pass


# TODO: main page, need to call separate helper methods here
@bp.route("/")
def display_main_page():
    with lock:
        # update the workers status before displaying
        update_workers_status()

    return render_template("main.html", num_workers=len(workers_map))


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


# up/down button invoked method, first verify the decision then pass over to change_workers_num to finish
@bp.route("/change_workers", methods=["POST"])
def change_workers():
    if request.method == "POST":
        with lock:
            if request.form.get("upBtn"):
                # make sure the decision is allowed
                decision = verify_decision(constants.INCREASE_DECISION)
                if decision != constants.INCREASE_DECISION:
                    flash("At most {} workers, please try to remove worker first".format(constants.MAX_WORKER_NUM), constants.ERROR)
                else:
                    # add worker
                    success = change_workers_num(True, 1)
                    if success:
                        flash("Successfully added a new worker to the pool", constants.INFO)
                    else:
                        flash("Failed to increase pool size, please try again later", constants.ERROR)
            elif request.form.get('downBtn'):
                # make sure the decision is allowed
                decision = verify_decision(constants.DECREASE_DECISION)
                if decision != constants.DECREASE_DECISION:
                    flash("At least {} workers, please try to increase worker first".format(constants.MIN_WORKER_NUM), constants.ERROR)
                else:
                    # remove worker
                    success = change_workers(False, 1)
                    if success:
                        flash("Successfully removed a new worker from the pool", constants.INFO)
                    else:
                        flash("Failed to decrease pool size, please try again later", constants.ERROR)
            else:
                flash("Invalid request to change worker pool size", constants.ERROR)
    return redirect(url_for("manager.display_main_page"))


# TODO: increase/decrease number of workers actual implementation
#   Yang idea: this should only be called by a method that wrapped in a lock, and the check
#   should be done before calling this method (caller should check in advance)
#   update the workers_map, ELB targets
def change_workers_num(is_increase: bool, changed_workers_num: int) -> bool:
    pass


# TODO: shut down all workers and the current manager app (close everything but keep data)
@bp.route("/terminate_manager", methods=["POST"])
def terminate_manager():
    flash("Successfully stopped the manager", constants.INFO)


# TODO: removed all application data including the images in S3 (not sure about the created users)
@bp.route("/remove_app_data", methods=["POST"])
def remove_app_data():
    flash("Successfully deleted all application data", constants.INFO)
    return redirect(url_for("manager.display_main_page"))


# verify if the decision is valid and output a final decision
def verify_decision(decision):
    if (decision == constants.INCREASE_DECISION and len(workers_map) == constants.MAX_WORKER_NUM) \
            or (decision == constants.DECREASE_DECISION and len(workers_map) == constants.MIN_WORKER_NUM):
        decision = constants.MAINTAIN_DECISION
    return decision


# TODO: update workers status and deregister/register them to ELB if necessary
def update_workers_status():
    pass
