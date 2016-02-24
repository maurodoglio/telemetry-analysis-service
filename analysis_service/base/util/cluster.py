from uuid import uuid4

from datetime import timedelta
from django.conf import settings
import boto3
import requests
from dateutil.parser import parse as parse_date

emr = boto3.client("emr", region_name=settings.AWS_CONFIG['AWS_REGION'])
ec2 = boto3.client("ec2", region_name=settings.AWS_CONFIG['AWS_REGION'])
ses = boto3.client("ses", region_name=settings.AWS_CONFIG['AWS_REGION'])
s3 = boto3.client("s3", region_name=settings.AWS_CONFIG['AWS_REGION'])


def spawn(user_email, identifier, size, public_key):
    """Given a user's email, a cluster identifier, a worker count, and a user public key,
    spawns a cluster with the desired properties and returns the jobflow ID."""
    # if the cluster is of size 1, we don't need to have a separate worker
    num_instances = size if size == 1 else size + 1

    # create the cluster/jobflow on Amazon EMR
    configurations = requests.get(
        "https://s3-{}.amazonaws.com/{}/configuration/configuration.json".format(
            settings.AWS_CONFIG["AWS_REGION"],
            settings.AWS_CONFIG["SPARK_EMR_BUCKET"]
        )
    ).json()
    cluster = emr.run_job_flow(
        Name=str(uuid4()),
        ReleaseLabel=settings.AWS_CONFIG['EMR_RELEASE'],
        Instances={
            'MasterInstanceType': settings.AWS_CONFIG['INSTANCE_TYPE'],
            'SlaveInstanceType': settings.AWS_CONFIG['INSTANCE_TYPE'],
            'InstanceCount': num_instances,
            'Ec2KeyName': 'mozilla_vitillo',
            'KeepJobFlowAliveWhenNoSteps': True,
        },
        JobFlowRole=settings.AWS_CONFIG["SPARK_INSTANCE_PROFILE"],
        ServiceRole='EMR_DefaultRole',
        Applications=[{'Name': 'Spark'}],
        Configurations=configurations,
        BootstrapActions=[{
            'Name': 'setup-telemetry-cluster',
            'ScriptBootstrapAction': {
                'Path': "s3://{}/bootstrap/telemetry.sh".format(
                    settings.AWS_CONFIG["SPARK_EMR_BUCKET"]
                ),
                'Args': ["--public-key", public_key]
            }
        }]
    )
    jobflow_id = cluster["JobFlowId"]

    # associate the jobflow with the user who launched it, the jobflow identifier,
    # and the Telemetry Analysis tag
    emr.add_tags(
        ResourceId=jobflow_id,
        Tags=[
            {'Key': 'Owner', 'Value': user_email},
            {'Key': 'Name', 'Value': identifier},
            {'Key': 'Application', 'Value': settings.AWS_CONFIG['INSTANCE_APP_TAG']},
        ]
    )

    return jobflow_id


def monitor(jobflow_id):
    cluster = emr.describe_cluster(ClusterId=jobflow_id)['Cluster']
    creation_time = cluster['Status']['Timeline']['CreationDateTime']
    return {
        "spawn_time": creation_time,
        "state":      cluster['Status']['State'],
        "public_dns": cluster['MasterPublicDnsName'],
        "kill_time":  get_termination_time(creation_time),
    }


def kill(jobflow_id):
    emr.terminate_job_flows(JobFlowIds=[jobflow_id])


def get_tag_value(tags, key):
    return next((tag.value for tag in tags if tag.key == key), None)


def get_termination_time(start_time):
    # Instance gets killed by terminate-expired-instances.py, 1 day after the creation time
    return parse_date(start_time, ignoretz=True) + timedelta(days=1)
