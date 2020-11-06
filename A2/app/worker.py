from datetime import datetime, timedelta

from app import aws_helper


# create a new worker by starting a EC2 instance, returns the instance_id
def create_worker(num):
    print("create worker, ", num)
    tag = {"Key": "Name", "Value": "Yang"}
    ec2 = aws_helper.session.resource("ec2", region_name="us-east-1")
    instances = ec2.create_instances(ImageId='ami-092e1ce5b6b7585ec', MinCount=num, MaxCount=num,
                                     SecurityGroupIds=['sg-09e21c9813da24aa1'], InstanceType='t2.medium',
                                     LaunchTemplate={
                                         'LaunchTemplateId': 'lt-032d46f563972b23d',
                                         'Version': '2'
                                     })
                        #              TagSpecifications=[{'ResourceType': 'instance',
                        # 'Tags': [tag]}])
    # TODO: to be removed later
    # instances[0].wait_until_running()
    return [instance.id for instance in instances]


# destroy the worker (can be used by the terminate and change worker num) by stopping the worker EC2 instance
def destroy_worker(instance_id):
    ec2 = aws_helper.session.client("ec2", region_name='us-east-1')
    response = ec2.terminate_instances(
        InstanceIds=[
            instance_id
        ]
    )


# register worker instance to the ELB, done by the auto-sclaer
def register_worker(instance_id):
    elb = aws_helper.session.client("elbv2", region_name='us-east-1')
    response = elb.register_targets(
        TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:752103853538:targetgroup/test8/7dcf9d434c066607',
        Targets=[
            {
                'Id': instance_id,
                'Port': 5000,
            },
        ]
    )


# deregister the worker instance from ELB, both manual shrink and auto-scaler can do it
def deregister_worker(instance_id):
    elb = aws_helper.session.client("elbv2", region_name='us-east-1')
    response = elb.deregister_targets(
        TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:752103853538:targetgroup/test8/7dcf9d434c066607',
        Targets=[
            {
                'Id': instance_id,
                'Port': 5000,
            },
        ]
    )


# call the worker to start the user app
def start_worker(instance_id):
    ssm_client = aws_helper.session.client('ssm', region_name='us-east-1')
    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={
            'commands': [
                'cd ~/Desktop/ECE1779_Projects/ECE1779/A1',
                'mkdir -p logs',
                '[ -e logs/access.log ] && rm logs/access.log',
                '[ -e logs/error.log ] && rm logs/error.log',
                './venv/bin/gunicorn -w 4 "app:create_app()" -e FLASK_ENV=production -b 0.0.0.0:5000 --access-logfile logs/access.log --error-logfile logs/error.log'
            ]
        })


def get_cpu_utilization(instance_id):
    cloudwatch = aws_helper.session.client("cloudwatch")
    cur_time = datetime.utcnow()
    cpu_utils_list = list()
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            },
        ],
        StartTime=cur_time - timedelta(seconds=1800),
        EndTime=cur_time,
        Period=60,
        Statistics=[
            "Average",
        ],
        Unit="Percent"
    )
    value = []
    for temp in response["Datapoints"]:
        value.append(temp["Average"])
    return value


def get_http_request(instance_id):

    cloudwatch = aws_helper.session.client("cloudwatch")
    cur_time = datetime.utcnow()
    response = cloudwatch.get_metric_statistics(
        Namespace="ECE1779/TRAFFIC",
        MetricName="Requests",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            },
        ],
        StartTime=cur_time - timedelta(seconds=1800),
        EndTime=cur_time,
        Period=60,
        Statistics=[
            "Sum"
        ],
        Unit="Count"
    )

    value = []
    for temp in response["Datapoints"]:
        value.append(temp["Sum"])

    return value


