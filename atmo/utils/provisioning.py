from uuid import uuid4

from django.conf import settings
import boto3
import requests

emr = boto3.client('emr', region_name=settings.AWS_CONFIG['AWS_REGION'])
ec2 = boto3.client('ec2', region_name=settings.AWS_CONFIG['AWS_REGION'])
s3 = boto3.client('s3', region_name=settings.AWS_CONFIG['AWS_REGION'])


def cluster_start(user_email, identifier, size, public_key, emr_release):
    """
    Given a user's email, a cluster identifier, a worker count, and a user
    public key, spawns a cluster with the desired properties and returns
    the jobflow ID.
    """
    # if the cluster is of size 1, we don't need to have a separate worker
    num_instances = size if size == 1 else size + 1

    # create the cluster/jobflow on Amazon EMR
    configurations = requests.get(
        'https://s3-{}.amazonaws.com/{}/configuration/configuration.json'.format(
            settings.AWS_CONFIG['AWS_REGION'],
            settings.AWS_CONFIG['SPARK_EMR_BUCKET']
        )
    ).json()

    # setup instance groups using spot market for slaves
    instance_groups = [
        {
            'Name': 'Master',
            'Market': 'ON_DEMAND',
            'InstanceRole': 'MASTER',
            'InstanceType': settings.AWS_CONFIG['MASTER_INSTANCE_TYPE'],
            'InstanceCount': 1
        }
    ]

    if num_instances > 1:
        instance_groups.append(
            {
                'Name': 'Slave Instances',
                'Market': 'SPOT',
                'InstanceRole': 'CORE',
                'InstanceType': settings.AWS_CONFIG['SLAVE_INSTANCE_TYPE'],
                'BidPrice': settings.AWS_CONFIG['CORE_SPOT_BID'],
                'InstanceCount': num_instances - 1
            }
        )

    cluster = emr.run_job_flow(
        Name=str(uuid4()),
        ReleaseLabel='emr-{}'.format(emr_release),
        Instances={
            'InstanceGroups': instance_groups,
            'Ec2KeyName': 'mozilla_vitillo',
            'KeepJobFlowAliveWhenNoSteps': True,  # same as no-auto-terminate
        },
        JobFlowRole=settings.AWS_CONFIG['SPARK_INSTANCE_PROFILE'],
        ServiceRole='EMR_DefaultRole',
        Applications=[{'Name': 'Spark'}, {'Name': 'Hive'}],
        Configurations=configurations,
        BootstrapActions=[{
            'Name': 'setup-telemetry-cluster',
            'ScriptBootstrapAction': {
                'Path': 's3://{}/bootstrap/telemetry.sh'.format(
                    settings.AWS_CONFIG['SPARK_EMR_BUCKET']
                ),
                'Args': ['--public-key', public_key]
            }
        }],
        Tags=[
            {'Key': 'Owner', 'Value': user_email},
            {'Key': 'Name', 'Value': identifier},
            {'Key': 'Application', 'Value': settings.AWS_CONFIG['INSTANCE_APP_TAG']},
        ],
        VisibleToAllUsers=True
    )

    return cluster['JobFlowId']


def cluster_rename(jobflow_id, new_identifier):
    emr.add_tags(
        ResourceId=jobflow_id,
        Tags=[
            {'Key': 'Name', 'Value': new_identifier},
        ]
    )


def cluster_info(jobflow_id):
    cluster = emr.describe_cluster(ClusterId=jobflow_id)['Cluster']
    creation_time = cluster['Status']['Timeline']['CreationDateTime']
    return {
        'start_time': creation_time,
        'state': cluster['Status']['State'],
        'public_dns': cluster.get('MasterPublicDnsName'),
    }


def cluster_stop(jobflow_id):
    emr.terminate_job_flows(JobFlowIds=[jobflow_id])
