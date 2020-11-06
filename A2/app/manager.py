"""
all manager related functionality is here, this is designed to be place to host
all manager functionality, the tasks dispatched by main module will enter here、
"""
from datetime import datetime, timedelta
from threading import Lock

from flask import Blueprint, flash, render_template, redirect, request, url_for

from app import aws_helper, constants, worker

bp = Blueprint("manager", __name__, url_prefix="/")
# shared by main thread and auto-scaler thread to prevent race condition
lock = Lock()
workers_map = dict()


# create a starting worker when app is started and maybe other initialization
# this should not require lock as we know this is running alone during app creation
def app_initialization():
    # retrieve credentials first
    aws_helper.check_credentials_expire()
    change_workers_num(True, 1)
    print("app init")


# main page, need to call separate helper methods here
@bp.route("/")
def display_main_page():
    with lock:
        # update the workers status before displaying
        update_workers_status()
        # workers_chart()
        labels = range(1, 31)
        values = get_num_worker()
        if len(values) == 0:
            values = [0] * 30
        print(workers_map)
    return render_template("main.html", num_workers=len(workers_map), workers=workers_map, max=8,
                           values=values, labels=labels)


# show the detailed information of the worker
@bp.route("/<instance_id>", methods=["POST"])
def get_worker_detail(instance_id):
    with lock:
        min = range(1, 31)
        cpu_util = worker.get_cpu_utilization(instance_id)
        http_rate = worker.get_http_request(instance_id)
    return render_template("worker_detail.html", mins=min, cpu=cpu_util,
                           time=min, rate=http_rate)


# use the auto-scaler keeps track of the number of the workers
#   track (it runs every minute), depends on your design
def workers_chart():
    return


def list_workers():
    with lock:
        update_workers_status()
    return


# up/down button invoked method, first verify the decision then pass over to change_workers_num to finish
@bp.route("/change_workers", methods=["POST"])
def change_workers():
    with lock:
        if request.method == "POST":
            if request.form.get("upBtn"):
                # make sure the decision is allowed
                decision = verify_decision(constants.INCREASE_DECISION)
                if decision != constants.INCREASE_DECISION:
                    flash("At most {} workers, please try to remove worker first".format(constants.MAX_WORKER_NUM),
                          constants.ERROR)
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
                    flash("At least {} workers, please try to increase worker first".format(constants.MIN_WORKER_NUM),
                          constants.ERROR)
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


#   increase/decrease number of workers actual implementation
def change_workers_num(is_increase: bool, changed_workers_num: int) -> bool:
    if len(workers_map) == constants.MAX_WORKER_NUM:
        flash("At most {} workers, please try to remove worker first".format(constants.MAX_WORKER_NUM),
              constants.ERROR)
        return False
    elif is_increase:
        if (len(workers_map) + changed_workers_num) > constants.MAX_WORKER_NUM:
            flash("There are already {} workers exits, too many workers created".format(len(workers_map)),
                  constants.ERROR)
            return False
        else:
            instance_ids = worker.create_worker(changed_workers_num)
            for instance_id in instance_ids:
                workers_map[instance_id] = constants.STARTING_STATE
                print(instance_id)
                return True
    else:
        if (len(workers_map) - changed_workers_num) < 1:
            flash("Can not downsize worker size to 0 ", constants.ERROR)
            return False
        else:
            stopping = 0
            inslist = []
            for ins, state in workers_map:
                if state == constants.STOPPING_STATE:
                    stopping += 1
                else:
                    inslist.append(ins)
            if (len(workers_map) - changed_workers_num - stopping) < 1:
                flash("Can not downsize worker size to 0 ", constants.ERROR)
                return False
            else:
                for num in range(changed_workers_num):
                    workers_map[inslist[num]] = constants.STOPPING_STATE
                    worker.deregister_worker(inslist[num])
                    worker.destroy_worker(inslist[num])
    return True


# shut down all workers and the current manager app (close everything but keep data)
@bp.route("/terminate_manager", methods=["POST"])
def terminate_manager():
    with lock:
        for instance_id, status in workers_map.items():
            if status == constants.RUNNING_STATE:
                worker.deregister_worker(instance_id)
                worker.destroy_worker(instance_id)
            elif status == constants.STARTING_STATE:
                worker.destroy_worker(instance_id)

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


# pull instance status from ec2 and update workers map status every 1 mins
# start app/ register elb accordingly
def update_workers_status():
    ec2 = aws_helper.session.resource("ec2")
        # TODO: suggestion - only retrieve the instances based on the worker map (faster)
    instances = ec2.instances.all()
    ids_set = set([instance.id for instance in instances])
    # TODO: only loop through the instances in worker map, then check if the instance_id is in ids_set (to check if its still there)
    for instance in instances:
        if instance.id in workers_map:
            if workers_map[instance.id] != instance.instance_type:
                # TODO: instance_type is t2.medium, you need to get instance status
                if workers_map[instance.id] == constants.STARTING_STATE and instance.instance_type == constants.RUNNING_STATE:
                    worker.start_worker(instance.id)
                    worker.register_worker(instance.id)
                    workers_map[instance.id] = constants.RUNNING_STATE
                if workers_map[instance.id] == constants.STOPPING_STATE and instance.instance_type == constants.TERMINATED_STATE:
                    del workers_map[instance.id]


def get_num_worker():
    cloudwatch = aws_helper.session.client("cloudwatch")
    cur_time = datetime.utcnow()
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/ApplicationELB",
        MetricName="HealthyHostCount",
        Dimensions=[
            {
                "Name": "LoadBalancer",
                "Value": "app/test7/2c8f8c35d8b2d055"
            },
        ],
        StartTime=cur_time - timedelta(seconds=1800),
        EndTime=cur_time,
        Period=60,
        Statistics=[
            "Average"
        ],
    )
    value = []
    for temp in response["Datapoints"]:
        value.append(temp["Average"])
    return value
