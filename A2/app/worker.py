"""
TODO: this is a place to do the worker specific job, executed per worker
"""


# TODO: get the worker details for one specific worker, show that worker detailed chart
def get_worker_detail():
    pass


# TODO: create a new worker by starting a EC2 instance
def create_worker():
    pass


# TODO: destroy the worker (can be used by the terminate and change worker num)
#   by stopping the worker EC2 instance
def destroy_worker():
    pass


# TODO: register worker instance to the ELB, done by the auto-sclaer
def register_worker():
    pass


# TODO: deregister the worker instance from ELB, both manual shrink and auto-scaler can do it
def deregister_worker():
    pass