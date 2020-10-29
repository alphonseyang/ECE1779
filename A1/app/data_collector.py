import time
from datetime import datetime
from http import HTTPStatus
from threading import Lock

import boto3
import requests

from app import constants

requests_count = 0
lock = Lock()
cloudwatch = boto3.client("cloudwatch")


# background thread that push the data to CloudWatch
def collect_requests_count(instance_id):
    while True:
        try:
            with lock:
                global requests_count
                current_timestamp = datetime.fromtimestamp((datetime.utcnow().timestamp() // 60 - 1) * 60)
                cloudwatch.put_metric_data(
                    MetricData=[{
                        'MetricName': 'Requests',
                        'Dimensions': [{
                            'Name': 'InstanceId',
                            'Value': instance_id
                        }],
                        'Timestamp': current_timestamp,
                        'Unit': 'Count',
                        'Value': requests_count
                    }],
                    Namespace='ECE1779/TRAFFIC'
                )
                print("INFO: the past one minute has {} requests, time {}".format(requests_count, current_timestamp))
                requests_count = 0
        except Exception as e:
            # for error log purpose
            print("ERROR: CloudWatch Collector Issue {}".format(e))
        finally:
            # execute every one minute
            time.sleep(constants.AUTO_COLLECT_WAIT_TIME)


# get the instance id to uniquely label the data points
def get_instance_id():
    if constants.IS_REMOTE:
        response = requests.get(constants.INSTANCE_ID_URL)
        if response.status_code != HTTPStatus.OK:
            return "remote"
        else:
            return response.content.decode()
    else:
        return "local"
