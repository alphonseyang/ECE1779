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
                # update the number of workers in the pool history
                manager.workers_num_history.insert(0, len(manager.workers_map))
                manager.workers_num_history.pop()

                # auto-scaler algorithm to check for decision
                decision, num = auto_scaler_make_decision()
                # based on the decision, start the action
                if decision == constants.INCREASE_DECISION:
                    manager.change_workers_num(True, num)
                    print("INFO: add {} new workers to the pool".format(num))
                elif decision == constants.DECREASE_DECISION:
                    manager.change_workers_num(False, num)
                    print("INFO: remove {} workers from the pool".format(num))
                elif decision == constants.MAINTAIN_DECISION:
                    print()
                else:
                    print("ERROR: unexpected auto-scaler decision {}".format(decision))
        except Exception as e:
            print(e)
        finally:
            # execute every one minute
            time.sleep(constants.AUTO_SCALING_WAIT_SECONDS)


# all logs to determine the auto-scaler is here
def auto_scaler_make_decision():
    decision = constants.MAINTAIN_DECISION
    # TODO: check the CPU average to determine the decision

    # verify if the decision is valid
    decision = manager.verify_decision(decision)
    # determine the number of workers change allowed
    num = determine_num_change(decision)

    return decision, num


# determine the num change based on the decision
def determine_num_change(decision):
    change_num = 0
    num_running = sum([1 for state in manager.workers_map.values() if state == constants.RUNNING_STATE])
    if decision == constants.INCREASE_DECISION:
        change_num = max(1, int((constants.EXPAND_RATIO - 1) * num_running))
    elif decision == constants.DECREASE_DECISION:
        change_num = max(1, int((constants.SHRINK_RATIO - 1) * num_running))
    return change_num
