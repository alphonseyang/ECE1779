"""
TODO: all manager related functionality is here, this is designed to be place to host
    all manager functionality, the tasks dispatched by main module will enter here
"""


# TODO: query the AWS to show the number of worker over the past 30 minutes
def workers_chart():
    pass


# TODO: list out the current workers with URLs and the DNS for AWS ELB
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

