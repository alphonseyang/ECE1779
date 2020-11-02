"""
TODO: this is a place to do the worker specific job, executed per worker
"""


# TODO: get the worker details for one specific worker, show that worker detailed chart

import json
from datetime import datetime, timedelta

import boto3
import dateutil.parser
import pytz
import requests
from boto3 import ec2


def get_worker_detail(instance_id):
    pass


# TODO: create a new worker by starting a EC2 instance, returns the instance_id
def create_worker():
    instance = ec2.create_instances(ImageId='ami-092e1ce5b6b7585ec', MinCount=1, MaxCount=1, SecurityGroupIds=['sg-09e21c9813da24aa1'], InstanceType='t2.medium')
    instance[0].wait_until_running()

    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=['instance[0].id'],
        DocumentName="AWS-RunShellScript",
        Parameters={
            'commands': [
                '#!/bin/bash',
                'cd ~/Desktop/ECE1779_Projects/ECE1779/A1',
                'mkdir -p logs',
                '[ -e logs/access.log ] && rm logs/access.log',
                '[ -e logs/error.log ] && rm logs/error.log',
                './venv/bin/gunicorn -w 4 "app:create_app()" -e FLASK_ENV=production -b 0.0.0.0:5000 --access-logfile logs/access.log --error-logfile logs/error.log'
            ]

        })

    return instance[0].id
    pass


# TODO: destroy the worker (can be used by the terminate and change worker num)
#   by stopping the worker EC2 instance
def destroy_worker(instance_id):
    response = boto3.client.terminate_instances(
        InstanceIds=[
            'instance_id'
        ]
    )


    pass


# TODO: register worker instance to the ELB, done by the auto-sclaer
def register_worker(instance_id):
    response = boto3.client.register_targets(
        TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:752103853538:targetgroup/test8/7dcf9d434c066607',
        Targets=[
            {
                'Id': 'instance_id',
                'Port': 5000,
                'AvailabilityZone': 'us-east-1a'
            },
        ]
    )
    pass


# TODO: deregister the worker instance from ELB, both manual shrink and auto-scaler can do it
def deregister_worker(instance_id):
    response = boto3.client.deregister_targets(
        TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:752103853538:targetgroup/test8/7dcf9d434c066607',
        Targets=[
            {
                'Id': 'instance_id',
                'Port': 5000,
                'AvailabilityZone': 'us-east-1a'
            },
        ]
    )

    pass
