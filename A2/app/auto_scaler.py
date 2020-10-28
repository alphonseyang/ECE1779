"""
TODO: this should be a background thread that monitors the
    ongoing workers using the CloudWatch API. When the monitored value
    changes, based on our threshold, call the AWS Elastic Load Balancing
    API to make change to add/remove workers
    1. this should be a long-running thread, running with manager app
    2. check the CPU utilization (CloudWatch) for each worker per minute
    3. worker size is 1 to 8
    4. every minute, check if the workers in the workers_map have changed, if so, update the workers_map
        for the start->running worker, register them to the ELB as well

    idea: start the EC2 first and record them in the workers_map with state,
    then every time we do the auto-scaling check or refresh the page or manually change,
    we can first check the workers map and make sure it is running properly and update it
"""
import time

from app import constants, manager


def start():
    while True:
        try:
            # use lock when updating the shared workers map
            with manager.lock:
                manager.workers_map = {1: 2}
                print(manager.workers_map)
        except Exception as e:
            print(e)
        finally:
            # execute every one minute
            time.sleep(constants.AUTO_SCALING_WAIT_SECONDS)


# TODO: check the past two minutes average for all workers to determine
def make_decision():
    pass
