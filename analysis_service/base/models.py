from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User

from analysis_service.base.util import provisioning, scheduling


class Cluster(models.Model):
    identifier = models.CharField(max_length=100)
    size = models.IntegerField()
    public_key = models.CharField(max_length=100000)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='cluster_created_by')
    jobflow_id = models.CharField(max_length=50, blank=True, null=True)

    most_recent_status = models.CharField(max_length=50, default="UNKNOWN")

    def __str__(self):
        return "<Cluster {}>".format(self.identifier)

    def __repr__(self):
        return "<Cluster {} {}>".format(self.identifier, self.size)

    def get_info(self):
        return provisioning.cluster_info(self.jobflow_id)

    def is_expiring_soon(self):
        """Returns true if the cluster is expiring in the next hour."""
        return self.end_date <= datetime.now() + timedelta(hours=1)

    def refresh_status(self):
        info = provisioning.cluster_info(self.jobflow_id)
        self.most_recent_status = info["state"]
        return self.most_recent_status

    def rename(self, new_identifier):
        provisioning.cluster_rename(self.jobflow_id, new_identifier)
        self.identifier = new_identifier

    def save(self, *args, **kwargs):
        """
        Insert the cluster into the database or update it if already present,
        spawning the cluster if it's not already spawned.
        """
        # actually start the cluster
        if not self.jobflow_id:
            self.jobflow_id = provisioning.cluster_start(
                self.created_by.email,
                self.identifier,
                self.size,
                self.public_key
            )

        # set the dates
        if not self.start_date:
            self.start_date = datetime.now()
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=1)  # clusters expire after 1 day

        return super(Cluster, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Remove the cluster from the database, shutting down the actual cluster."""
        if self.jobflow_id:
            provisioning.cluster_stop(self.jobflow_id)

        return super(Cluster, self).delete(*args, **kwargs)


class Worker(models.Model):
    identifier = models.CharField(max_length=100)
    public_key = models.CharField(max_length=100000)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='worker_created_by')
    instance_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return "<Worker {}>".format(self.identifier)

    def __repr__(self):
        return "<Worker {}>".format(self.identifier)

    def get_info(self):
        return provisioning.worker_info(self.instance_id)

    def save(self, *args, **kwargs):
        # actually start the worker
        if not self.instance_id:
            self.instance_id = provisioning.worker_start(
                self.created_by.email,
                self.identifier,
                self.public_key
            )

        # set the dates
        if not self.start_date:
            self.start_date = datetime.now()
        if not self.end_date:
            self.end_date = datetime.now() + timedelta(days=1)  # workers expire after 1 day
        return super(Cluster, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        provisioning.worker_stop(self.worker_id)

        return super(Cluster, self).delete(*args, **kwargs)


class ScheduledSpark(models.Model):
    identifier = models.CharField(max_length=100)
    notebook_s3_key = models.CharField(max_length=800)
    result_visibility = models.CharField(max_length=50)  # can currently be "private" or "public"
    size = models.IntegerField()
    interval_in_hours = models.IntegerField()
    job_timeout = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_enabled = models.BooleanField(default=True)
    last_run_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='scheduled_spark_created_by')

    def __str__(self):
        return "<ScheduledSpark {}>".format(self.identifier)

    def __repr__(self):
        return "<ScheduledSpark {} {}>".format(self.identifier, self.size)

    def should_run(self, at_time = None):
        """Return True if the scheduled Spark job should run, False otherwise."""
        if at_time is None:
            at_time = datetime.now()
        active = self.start_date <= at_time <= self.end_date
        hours_since_last_run = (
            float("inf")
            if self.last_run_date is None else
            (at_time - self.last_run_date).total_seconds() / 3600
        )
        can_run_now = hours_since_last_run >= self.interval_in_hours
        return self.enabled and active and can_run_now

    def run(self):
        """Actually run the scheduled Spark job."""
        scheduling.scheduled_spark_run(
            self.created_by.email,
            self.identifier,
            self.notebook_s3_key,
            self.result_visibility == "public",
            self.size,
            self.job_timeout
        )

    def save(self, notebook_uploadedfile = None, *args, **kwargs):
        if notebook_uploadedfile is not None:  # notebook specified, replace current notebook
            self.notebook_s3_key = scheduling.scheduled_spark_add(
                self.identifier,
                notebook_uploadedfile
            )
        return super(Cluster, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        scheduling.scheduled_spark_remove(self.notebook_s3_key)

        super(ScheduledSpark, self).delete(*args, **kwargs)
