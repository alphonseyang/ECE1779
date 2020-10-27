"""
TODO: all manager related functionality is here, this is designed to be place to host
    all manager functionality, the tasks dispatched by main module will enter here
"""
from threading import Lock


# shared by main thread and auto-scaler thread to prevent race condition
lock = Lock()
workers_map = dict()


# TODO: create a starting worker when app is started
def app_initialization():
    pass


# TODO: query the AWS to show the number of worker over the past 30 minutes
def workers_chart():
    pass


# TODO: list out the current workers with URLs and the DNS for AWS ELB
#   show the state of the instance (stopping and starting ones are considered working node)
def list_workers():
    pass


# TODO: increase/decrease number of workers, be aware the min/max workers allowed
def change_workers_num():
    pass


# TODO: shut down all workers and the current manager app (close everything but keep data)
def terminate_manager():
    pass


# TODO: removed all application data including the images in S3 (not sure about the created users)
def remove_app_data():
    pass
