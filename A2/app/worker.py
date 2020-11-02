from flask import Blueprint, flash, render_template, redirect, request, url_for
from app import aws_helper, constants
import numpy as np
import time
from datetime import datetime, timedelta
from http import HTTPStatus

from app.manager import lock

bp = Blueprint("manager", __name__, url_prefix="/")


# TODO: get the worker details for one specific worker, show that worker detailed chart
@bp.route("/<instance_id>")
def get_worker_detail(instance_id):
    with lock:
        min = np.arange(1, 31)
        cpu_util = get_cpu_utilization(instance_id)
        http_rate = get_http_request(instance_id)
    return render_template("worker_detail.html", mins=min, cpu=cpu_util,
                           time=min, rate=http_rate)


# TODO: create a new worker by starting a EC2 instance, returns the instance_id
def create_worker():
    pass


# TODO: destroy the worker (can be used by the terminate and change worker num)
#   by stopping the worker EC2 instance
def destroy_worker(instance_id):
    pass


# TODO: register worker instance to the ELB, done by the auto-sclaer
def register_worker(instance_id):
    pass


# TODO: deregister the worker instance from ELB, both manual shrink and auto-scaler can do it
def deregister_worker(instance_id):
    pass


def get_cpu_utilization(instance_id):
    cloudwatch = aws_helper.session.client("cloudwatch")
    cur_time = datetime.utcnow()
    cpu_utils_list = list()
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            },
        ],
        StartTime=cur_time - timedelta(seconds=1800),
        EndTime=cur_time,
        Period=60,
        Statistics=[
            "Average",
        ],
        Unit="Percent"
    )
    return response["Datapoints"]["Average"]


def get_http_request(instance_id):
    cloudwatch = aws_helper.session.client("cloudwatch")
    cur_time = datetime.utcnow()
    response = cloudwatch.get_metric_statistics(
        Namespace="ECE1779/TRAFFIC",
        MetricName="Requests",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            },
        ],
        StartTime=cur_time - timedelta(seconds=1800),
        EndTime=cur_time,
        Period=60,
        Statistics=[
            "SampleCount"
        ],
        Unit="Count"
    )
    return response



