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
EXPAND_RATIO = 2
SHRINK_RATIO = 2

# constants related to the worker state
RUNNING_STATE = "running"
STARTING_STATE = "starting"
TERMINATING_STATE = "terminating"
