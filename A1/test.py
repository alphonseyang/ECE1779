import os

# the combination to trigger the number of workers required in auto-scaling
load1 = [1, 900]
load2 = [4, 3600]
load3 = [6, 5400]
run_command = 'python3 gen.py http://test7-361718708.us-east-1.elb.amazonaws.com/api/upload root root {} ./app/static/images/test/ {}'

cases = [load1]
for per_second, total in cases:
    command = run_command.format(per_second, total)
    os.system(command)
