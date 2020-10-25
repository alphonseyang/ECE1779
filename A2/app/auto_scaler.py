"""
TODO: this should be a background thread that monitors the
    ongoing workers using the CloudWatch API. When the monitored value
    changes, based on our threshold, call the AWS Elastic Load Balancing
    API to make change to add/remove workers
    1. this should be a long-running thread, running with manager app
    2. check the CPU utilization (CloudWatch) for each worker per minute
    3. worker size is 1 to 8
"""