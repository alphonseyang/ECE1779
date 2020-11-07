"""
this should be a background thread that monitors the
ongoing workers using the CloudWatch API. When the monitored value
changes, based on our threshold, call the manager module helper methods
 to make change to add/remove workers
1. this should be a long-running thread, running with manager app
2. check the CPU utilization (CloudWatch) for each worker per minute
3. worker size is 1 to 8
4. every minute, check if the workers in the workers_map have changed, if so, update the workers_map
    for the start->running worker

idea: start the EC2 first and record them in the workers_map with state,
then every time we do the auto-scaling check or refresh the page or manually change,
we can first check the workers map and make sure it is running properly and update it
"""
import time
from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, flash, render_template, request, redirect, url_for

from app import aws_helper, constants, database, manager

bp = Blueprint("auto_scaler", __name__, url_prefix="/autoscaler")


@bp.route("/", methods=("GET", "POST"))
def auto_scaler_policy():
    policy = get_auto_scaler_policy()
    if request.method == "POST":
        with manager.lock:
            try:
                expand_ratio = request.form.get("expand_ratio")
                shrink_ratio = request.form.get("shrink_ratio")
                grow_threshold = request.form.get("grow_threshold")
                shrink_threshold = request.form.get("shrink_threshold")
                is_valid, error = validate_input_policy(expand_ratio, shrink_ratio, grow_threshold, shrink_threshold)
                if not is_valid:
                    flash(error, constants.ERROR)
                    return redirect(url_for(request.url))
                policy[constants.EXPAND_RATIO] = float(expand_ratio) if expand_ratio else policy[constants.EXPAND_RATIO]
                policy[constants.SHRINK_RATIO] = float(shrink_ratio) if shrink_ratio else policy[constants.SHRINK_RATIO]
                policy[constants.CPU_UTIL_GROW_THRESHOLD] = int(grow_threshold) if grow_threshold else policy[constants.CPU_UTIL_GROW_THRESHOLD]
                policy[constants.CPU_UTIL_SHRINK_THRESHOLD] = int(shrink_threshold) if shrink_threshold else policy[constants.CPU_UTIL_SHRINK_THRESHOLD]
                db_conn = database.get_conn()
                cursor = db_conn.cursor()
                sql_stmt = '''UPDATE policy SET expand_ratio={}, shrink_ratio={}, cpu_util_grow_threshold={}, 
                            cpu_util_shrink_threshold={} WHERE policy_id=1'''.format(
                    policy[constants.EXPAND_RATIO], policy[constants.SHRINK_RATIO],
                    policy[constants.CPU_UTIL_GROW_THRESHOLD], policy[constants.CPU_UTIL_SHRINK_THRESHOLD]
                )
                cursor.execute(sql_stmt)
                db_conn.commit()
                flash("Successfully update Auto-Scaler policy", constants.INFO)
            except Exception as e:
                flash("Failed to update Auto-Scaler policy, please try again", constants.ERROR)
            return redirect(url_for("auto_scaler.auto_scaler_policy"))

    return render_template("auto_scaler.html", policy=policy)


# main auto-scaler background thread method
def start():
    while True:
        try:
            # use lock when updating the shared workers map
            with manager.lock:
                # update the number of workers in the pool history

                # auto-scaler algorithm to check for decision
                decision, num = auto_scaler_make_decision()
                success = True
                # based on the decision, start the action
                if decision == constants.INCREASE_DECISION:
                    success = manager.change_workers_num(True, num)
                    print("INFO: add {} new workers to the pool".format(num))
                elif decision == constants.DECREASE_DECISION:
                    success = manager.change_workers_num(False, num)
                    print("INFO: remove {} workers from the pool".format(num))
                elif decision == constants.MAINTAIN_DECISION:
                    print("INFO: no auto-scaling change in the worker pool")
                else:
                    print("ERROR: unexpected auto-scaler decision {}".format(decision))
                if not success:
                    print("ERROR: issue with change_workers_num, please investigate")
        except Exception as e:
            print("ERROR: unexpected error {}".format(e))
        finally:
            # execute every one minute
            time.sleep(constants.AUTO_SCALING_WAIT_SECONDS)
            # check for credentials, if not available, retrieve it
            aws_helper.check_credentials_expire()


# all logs to determine the auto-scaler is here
def auto_scaler_make_decision():
    # re-check the status of the instances in workers pool to ensure they are updated
    manager.update_workers_status()
    policy = get_auto_scaler_policy()

    # check the CPU average to determine the decision
    decision = constants.MAINTAIN_DECISION
    cpu_utilization_avg = get_cpu_utilization_average()
    if cpu_utilization_avg != -1:
        if cpu_utilization_avg >= policy[constants.CPU_UTIL_GROW_THRESHOLD]:
            decision = constants.INCREASE_DECISION
        elif cpu_utilization_avg <= policy[constants.CPU_UTIL_SHRINK_THRESHOLD]:
            decision = constants.DECREASE_DECISION

    # verify if the decision is valid
    decision = manager.verify_decision(decision)
    # determine the number of workers change allowed
    num = determine_num_change(decision, policy)

    return decision, num


# compute cpu utilization average for past 2 minutes
def get_cpu_utilization_average():
    cloudwatch = aws_helper.session.client("cloudwatch")
    cur_time = datetime.utcnow()
    cpu_utils_list = list()
    for instance_id in manager.workers_map:
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[
                {
                    "Name": "InstanceId",
                    "Value": instance_id
                },
            ],
            StartTime=cur_time - timedelta(seconds=120),
            EndTime=cur_time,
            Period=60,
            Statistics=[
                "Average",
            ],
            Unit="Percent"
        )
        if response.get("ResponseMetadata", dict()).get("HTTPStatusCode") == HTTPStatus.OK and len(response.get("Datapoints")) > 0:
            cpu_utilization_avg = sum([point["Average"] for point in response["Datapoints"]]) / len(response["Datapoints"])
            cpu_utils_list.append(cpu_utilization_avg)
        else:
            cpu_utils_list.append(0)
    if len(cpu_utils_list) > 0:
        avg_cpu_util = sum(cpu_utils_list) / len(cpu_utils_list)
        return avg_cpu_util if avg_cpu_util > 0 else -1
    else:
        return -1


# determine the num change based on the decision
def determine_num_change(decision, policy):
    change_num = 0
    total_instances = len(manager.workers_map)
    num_starting = sum([1 for state in manager.workers_map.values() if state == constants.STARTING_STATE])
    num_stopping = sum([1 for state in manager.workers_map.values() if state == constants.STOPPING_STATE])

    # determine the number of workers to increase/decrease, then check if there are some working on it now
    # if some already pending, just do the remaining, also prevent grow/shrink too many times
    if decision == constants.INCREASE_DECISION:
        change_num = max(1, int(policy[constants.EXPAND_RATIO] - 1) * total_instances)
        change_num = max(0, change_num - num_starting)
    elif decision == constants.DECREASE_DECISION:
        change_num = max(1, total_instances * policy[constants.SHRINK_RATIO])
        change_num = max(0, change_num - num_stopping)

    return int(change_num)


# get the auto scaler policy from the database
def get_auto_scaler_policy():
    try:
        db_conn = database.get_conn()
        cursor = db_conn.cursor()
        cursor.execute("SELECT expand_ratio, shrink_ration, cpu_util_grow_threshold, cpu_util_shrink_threshold FROM policy")
        policy = cursor.fetchone()
        policy = policy if policy else constants.DEFAULT_POLICY
        db_conn.commit()
        return list(policy)
    except Exception as e:
        return constants.DEFAULT_POLICY


def validate_input_policy(expand_ratio, shrink_ratio, grow_threshold, shrink_threshold):
    if expand_ratio and float(expand_ratio) <= 1:
        return False, "Expand Ratio must be larger than 1"
    if shrink_ratio and 0 >= float(shrink_ratio) >= 1:
        return False, "Shrink Ration must between 0 and 1"
    if grow_threshold and 0 > int(grow_threshold) > 100:
        return False, "CPU Utilization Grow Threshold must between 0 and 100"
    if shrink_threshold and 0 > int(shrink_threshold) > 100:
        return False, "CPU Utilization Shrink Threshold must between 0 and 100"
    if grow_threshold and shrink_threshold and int(grow_threshold) - 10 < int(shrink_threshold):
        return False, "Grow Threshold must be at least 10% higher than Shrink Threshold"
    return True, None
