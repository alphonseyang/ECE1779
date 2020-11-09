# constants related to flashed message type
ERROR = "error"
INFO = "info"

# constants used by auto scaler
MAX_WORKER_NUM = 8
MIN_WORKER_NUM = 1
AUTO_SCALING_WAIT_SECONDS = 60
INCREASE_DECISION = 0
DECREASE_DECISION = 1
MAINTAIN_DECISION = 2
EXPAND_RATIO = 0
SHRINK_RATIO = 1
CPU_UTIL_GROW_THRESHOLD = 2
CPU_UTIL_SHRINK_THRESHOLD = 3
DEFAULT_POLICY = [2, 0.5, 60, 10]


# constants related to the worker state
RUNNING_STATE = "running"
STARTING_STATE = "pending"
STOPPING_STATE = "stopping"
TERMINATED_STATE = "terminated"

# constants for AWS related
# TODO: update this to True before deployment
IS_REMOTE = True
ROLE_CREDENTIALS_URL = "http://169.254.169.254/latest/meta-data/iam/security-credentials/ECE1779YangWangKuang-ManagerRole"
BUCKET_NAME = "ece1779yangkuangwang-bucket"
LOAD_BALANCER_ARN = "arn:aws:elasticloadbalancing:us-east-1:752103853538:loadbalancer/app/test7/2c8f8c35d8b2d055"
