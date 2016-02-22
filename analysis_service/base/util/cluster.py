from uuid import uuid4

from django.conf import settings
import boto3
import requests

emr = boto3.client("emr", region_name=settings.AWS_CONFIG['AWS_REGION'])
ec2 = boto3.client("ec2", region_name=settings.AWS_CONFIG['AWS_REGION'])
ses = boto3.client("ses", region_name=settings.AWS_CONFIG['AWS_REGION'])
s3 = boto3.client("s3", region_name=settings.AWS_CONFIG['AWS_REGION'])

def spawn(user_email, identifier, size, public_key):
    """Given a user's email, a cluster identifier, a worker count, and a user public key, spawns a cluster with the desired properties and returns the jobflow ID."""
    # Create EMR cluster
    num_instances = size if size == 1 else size + 1 # if the cluster is of size 1, we don't need to have a separate worker
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
            'KeepJobFlowAliveWhenNoSteps':True,
        },
        JobFlowRole=settings.AWS_CONFIG["SPARK_INSTANCE_PROFILE"],
        ServiceRole='EMR_DefaultRole',
        Applications=[{'Name': 'Spark'}],
        Configurations=configurations,
        BootstrapActions=[{
            'Name': 'setup-telemetry-cluster',
            'ScriptBootstrapAction': {
                'Path': "s3://{}/bootstrap/telemetry.sh".format(settings.AWS_CONFIG["SPARK_EMR_BUCKET"]),
                'Args': ["--public-key", public_key]
            }
        }]
    )
    jobflow_id = cluster["ClusterId"]

    # Associate a few tags
    emr.add_tags(jobflow_id, {
        "Owner": user_email,
        "Name": identifier,
        "Application": settings.AWS_CONFIG['INSTANCE_APP_TAG']
    })

    # Send an email to the user who launched it
    params = {
        'monitoring_url': abs_url_for('cluster_monitor', jobflow_id = jobflow_id)
    }
    ses.send_email(
        source = app.config['EMAIL_SOURCE'],
        subject = ("telemetry-analysis cluster: %s (%s) launched" % (request.form['name'], jobflow_id)),
        format = 'html',
        body = render_template('cluster/email.html', **params),
        to_addresses = [current_user.email]
    )

    return jobflow_id
