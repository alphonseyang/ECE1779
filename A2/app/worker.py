from datetime import datetime, timedelta

import numpy as np
from flask import Blueprint, render_template

from app import aws_helper
from app.manager import lock

bp = Blueprint("manager", __name__, url_prefix="/")


# show the detailed information of the worker
@bp.route("/<instance_id>")
def get_worker_detail(instance_id):
    with lock:
        min = np.arange(1, 31)
        cpu_util = get_cpu_utilization(instance_id)
        http_rate = get_http_request(instance_id)
    return render_template("worker_detail.html", mins=min, cpu=cpu_util,
                           time=min, rate=http_rate)


# create a new worker by starting a EC2 instance, returns the instance_id
def create_worker():
    ec2 = aws_helper.session.resource("ec2")
    instance = ec2.create_instances(ImageId='ami-092e1ce5b6b7585ec', MinCount=1, MaxCount=1,
                                    SecurityGroupIds=['sg-09e21c9813da24aa1'], InstanceType='t2.medium')
    return instance[0].id


# destroy the worker (can be used by the terminate and change worker num) by stopping the worker EC2 instance
def destroy_worker(instance_id):
    ec2 = aws_helper.session.client("ec2")
    response = ec2.terminate_instances(
        InstanceIds=[
            instance_id
        ]
    )


# register worker instance to the ELB, done by the auto-sclaer
def register_worker(instance_id):
    elb = aws_helper.session.client("elbv2")
    response = elb.register_targets(
        TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:752103853538:targetgroup/test8/7dcf9d434c066607',
        Targets=[
            {
                'Id': instance_id,
                'Port': 5000,
                'AvailabilityZone': 'us-east-1a'
            },
        ]
    )


# deregister the worker instance from ELB, both manual shrink and auto-scaler can do it
def deregister_worker(instance_id):
    elb = aws_helper.session.client("elbv2")
    response = elb.deregister_targets(
        TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:752103853538:targetgroup/test8/7dcf9d434c066607',
        Targets=[
            {
                'Id': instance_id,
                'Port': 5000,
                'AvailabilityZone': 'us-east-1a'
            },
        ]
    )


# call the worker to start the user app
def start_worker(instance_id):
    ssm_client = aws_helper.session.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={
            'commands': [
                'cd ~/Desktop/ECE1779_Projects/ECE1779/A1',
                'mkdir -p logs',
                '[ -e logs/access.log ] && rm logs/access.log',
                '[ -e logs/error.log ] && rm logs/error.log',
                './venv/bin/gunicorn -w 4 "app:create_app()" -e FLASK_ENV=production -b 0.0.0.0:5000 --access-logfile logs/access.log --error-logfile logs/error.log'
            ]
        })


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
