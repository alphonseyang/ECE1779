from datetime import datetime, timedelta

from app import aws_helper


# create a new worker by starting a EC2 instance, returns the instance_id
def create_worker(num):
    print("create worker, ", num)
    ec2 = aws_helper.session.resource("ec2", region_name="us-east-1")
    instances = ec2.create_instances(ImageId='ami-0dc4da91f8429c09c', MinCount=num, MaxCount=num,
                                     SecurityGroupIds=['sg-09e21c9813da24aa1'], InstanceType='t2.small',
                                     LaunchTemplate={
                                         'LaunchTemplateId': 'lt-0556f998666a52f4e',
                                         'Version': '6'
                                     })
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
    sorted_d = []
    if len(response["Datapoints"]) != 0:
        sorted_d = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
        for temp in sorted_d:
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
    sorted_d = []
    if len(response["Datapoints"]) != 0:
        sorted_d = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
        for temp in sorted_d:
            value.append(temp["Sum"])

    return value


