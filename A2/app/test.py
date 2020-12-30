import boto3
from datetime import datetime, timedelta
from http import HTTPStatus

cloudwatch = boto3.client("cloudwatch")
cur_time = datetime.utcnow()
cpu_utils_list = list()
for instance_id in ["i-0322caea745992c6b"]:
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            },
        ],
        StartTime=cur_time - timedelta(seconds=180),
        EndTime=cur_time,
        Period=60,
        Statistics=[
            "Average",
        ],
        Unit="Percent"
    )
    datapoints = response.get("Datapoints", list())
    if len(datapoints) > 2:
        datapoints.sort(key=lambda x: x["Timestamp"])
        datapoints = datapoints[-2:]
    if response.get("ResponseMetadata", dict()).get("HTTPStatusCode") == HTTPStatus.OK and len(datapoints) > 0:
        cpu_utilization_avg = sum([point["Average"] for point in datapoints]) / len(datapoints)
        cpu_utils_list.append(cpu_utilization_avg)
    else:
        cpu_utils_list.append(0)
if len(cpu_utils_list) > 0:
    avg_cpu_util = sum(cpu_utils_list) / len(cpu_utils_list)
else:
    avg_cpu_util = -1
print(avg_cpu_util)