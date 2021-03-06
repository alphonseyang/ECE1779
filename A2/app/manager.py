"""
all manager related functionality is here, this is designed to be place to host
all manager functionality, the tasks dispatched by main module will enter here、
"""
import sys
from collections import OrderedDict
from datetime import datetime, timedelta
from threading import Lock

from flask import Blueprint, flash, render_template, redirect, request, url_for

from app import aws_helper, constants, database, worker

bp = Blueprint("manager", __name__, url_prefix="/")
# shared by main thread and auto-scaler thread to prevent race condition
lock = Lock()
workers_map = OrderedDict()


# create a starting worker when app is started and maybe other initialization
# this should not require lock as we know this is running alone during app creation
def app_initialization():
    # retrieve credentials first
    aws_helper.check_credentials_expire()
    change_workers_num(True, 1)
    print("INFO: app initialized successfully")


# main page, need to call separate helper methods here
@bp.route("/")
def display_main_page():
    with lock:
        # update the workers status before displaying
        update_workers_status()
        # workers_chart()
        labels = range(30, 0, -1)
        values = get_num_worker()
        print("INFO: Current workers: {}".format(workers_map))
    dns_name = get_load_balancer_dns()

    return render_template("main.html", num_workers=len(workers_map), workers=workers_map, max=8,
                           values=values, labels=labels, dns_name=dns_name)


# show the detailed information of the worker
@bp.route("/<instance_id>", methods=["POST"])
def get_worker_detail(instance_id):
    with lock:
        minutes = range(30, 0, -1)
        max1 = 100
        cpu_util = worker.get_cpu_utilization(instance_id)
        http_rate = worker.get_http_request(instance_id)
        max2 = max(http_rate) + 1

    return render_template("worker_detail.html", cpu=cpu_util, max1=max1, max2=max2, time=minutes, rate=http_rate)


# up/down button invoked method, first verify the decision then pass over to change_workers_num to finish
@bp.route("/change_workers", methods=["POST"])
def change_workers():
    with lock:
        if request.method == "POST":
            if request.form.get("upBtn"):
                print("INFO: Adding new worker")
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
                print("INFO: Removing worker")
                # make sure the decision is allowed
                decision = verify_decision(constants.DECREASE_DECISION)
                if decision != constants.DECREASE_DECISION:
                    flash("At least {} workers, please try to increase worker first".format(constants.MIN_WORKER_NUM),
                          constants.ERROR)
                else:
                    # remove worker
                    success = change_workers_num(False, 1)
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
                print("INFO: Successfully created new worker with id {}".format(instance_id))
            return True
    else:
        if (len(workers_map) - changed_workers_num) < 1:
            flash("Cannot downsize worker size to 0 ", constants.ERROR)
            return False
        else:
            stopping = 0
            inslist = []
            for instance_id, status in workers_map.items():
                if status == constants.STOPPING_STATE:
                    stopping += 1
                else:
                    inslist.append(instance_id)
            if (len(workers_map) - changed_workers_num - stopping) < 1:
                flash("Cannot downsize worker size to 0 ", constants.ERROR)
                return False
            else:
                for i in range(changed_workers_num):
                    instance_id = inslist.pop()
                    workers_map[instance_id] = constants.STOPPING_STATE
                    worker.deregister_worker(instance_id)
                    worker.destroy_worker(instance_id)
    return True


# terminate all workers and stop the current manager instance (close everything but keep data)
@bp.route("/terminate_manager", methods=["POST"])
def terminate_manager():
    database.get_conn().close()
    if constants.IS_REMOTE:
        clean_all_workers()
        ec2 = aws_helper.session.client("ec2")
        ec2.stop_instances(InstanceIds=['i-0d92ec486e6faeb22'])
        sys.exit(4)
    else:
        shutdown = request.environ.get("werkzeug.server.shutdown")
        if not shutdown:
            flash("Failed to terminate manager app", constants.ERROR)
            return
        clean_all_workers()
        shutdown()
    return redirect(url_for("manager.display_main_page"))


# helper method to clear all workers when invoked by the terminate_manager method
def clean_all_workers():
    with lock:
        for instance_id, status in workers_map.items():
            if status == constants.RUNNING_STATE:
                worker.deregister_worker(instance_id)
                worker.destroy_worker(instance_id)
            elif status == constants.STARTING_STATE:
                worker.destroy_worker(instance_id)


# removed all application data including the images in S3 (not sure about the created users)
@bp.route("/remove_app_data", methods=["POST"])
def remove_app_data():
    try:
        s3 = aws_helper.session.resource('s3')
        bucket = s3.Bucket(constants.BUCKET_NAME)
        bucket.objects.all().delete()
        db_conn = database.get_conn()
        cursor = db_conn.cursor()
        sql_script = open("app/static/schema.sql")
        sql_commands = sql_script.read().split(";")
        for command in sql_commands:
            command = command.replace("\n", "")
            if command:
                cursor.execute(command)
        db_conn.commit()
    except Exception as e:
        flash("Failed to remove application data, please try again", constants.ERROR)
    else:
        flash("Successfully removed application data", constants.INFO)
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
    instances = ec2.instances.all()
    terminate_worker = []
    start_worker = []
    for instance in instances:
        if instance.id in workers_map:
            if workers_map[instance.id] != instance.state['Name']:
                if workers_map[instance.id] == constants.STARTING_STATE and \
                        instance.state['Name'] == constants.RUNNING_STATE:
                    start_worker.append(instance.id)
                if workers_map[instance.id] == constants.STOPPING_STATE and \
                        instance.state['Name'] == constants.TERMINATED_STATE:
                    terminate_worker.append(instance.id)

    for ins in start_worker:
        worker.register_worker(ins)
        workers_map[ins] = constants.RUNNING_STATE
    for ins in terminate_worker:
        del workers_map[ins]


# get the number of workers based on the ELB healthy host count
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
            {
                "Name": "TargetGroup",
                "Value": "targetgroup/test8/7dcf9d434c066607"
            }
        ],
        StartTime=cur_time - timedelta(seconds=1800),
        EndTime=cur_time,
        Period=60,
        Statistics=[
            "Average"
        ],
    )
    value = [0] * 30
    if len(response["Datapoints"]) != 0:
        sorted_d = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
        for i in range(len(sorted_d)):
            if i == 30: break
            # value index, provides offset
            vi = i + 30 - len(sorted_d)
            value[vi] = sorted_d[i]["Average"]
    return value


# get the DNS name for display
def get_load_balancer_dns():
    elb = aws_helper.session.client("elbv2")
    response = elb.describe_load_balancers(LoadBalancerArns=[constants.LOAD_BALANCER_ARN])
    dns_name = response["LoadBalancers"][0]["DNSName"]
    return dns_name
