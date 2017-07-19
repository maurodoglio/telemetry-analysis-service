# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
from datetime import timedelta

import pytest
from celery.exceptions import Retry
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time

from atmo.clusters.models import Cluster
from atmo.jobs import exceptions, schedules, tasks
from atmo.stats.models import Metric


def test_run_job_not_exists():
    with pytest.raises(exceptions.SparkJobNotFound):
        tasks.run_job(1234)


def test_run_job_get_spark_job(spark_job):
    assert spark_job.pk == tasks.run_job.get_spark_job(spark_job.pk).pk


def test_run_job_without_run_status_updated(mocker, spark_job,
                                            cluster_provisioner_mocks):
    run = mocker.patch('atmo.jobs.models.SparkJob.run')
    refresh_from_db = mocker.patch('atmo.jobs.models.SparkJob.refresh_from_db')

    assert not spark_job.latest_run
    mocker.spy(tasks.run_job, 'sync_run')
    sync = mocker.patch('atmo.jobs.models.SparkJobRun.sync')

    tasks.run_job(spark_job.pk)

    # tries to update the status
    assert tasks.run_job.sync_run.call_count == 1
    # update does not really do it, since there wasn't a previous run
    assert sync.call_count == 0
    # no need to refresh the object
    assert refresh_from_db.call_count == 0
    # but run anyway
    assert run.call_count == 1


def test_run_job_with_run_status_updated(mocker, spark_job_with_run_factory,
                                         cluster_provisioner_mocks):
    run = mocker.patch('atmo.jobs.models.SparkJob.run')
    refresh_from_db = mocker.patch('atmo.jobs.models.SparkJob.refresh_from_db')
    spark_job_with_run = spark_job_with_run_factory(
        run__status=Cluster.STATUS_TERMINATED,
    )

    assert spark_job_with_run.latest_run
    mocker.spy(tasks.run_job, 'sync_run')
    sync = mocker.patch('atmo.jobs.models.SparkJobRun.sync')

    tasks.run_job(spark_job_with_run.pk)

    assert tasks.run_job.sync_run.call_count == 1
    assert sync.call_count == 1
    assert refresh_from_db.call_count == 1
    assert run.call_count == 1


def test_run_job_not_enabled(mocker, spark_job_with_run_factory,
                             cluster_provisioner_mocks):
    spark_job_with_run = spark_job_with_run_factory(is_enabled=False)
    mocker.spy(tasks.run_job, 'check_enabled')
    with pytest.raises(exceptions.SparkJobNotEnabled):
        tasks.run_job(spark_job_with_run.pk)
    assert tasks.run_job.check_enabled.call_count == 1


def test_run_job_expired_job(mocker, one_hour_ahead, spark_job_with_run_factory,
                             cluster_provisioner_mocks):
    # create a job that is not due to run, e.g. the start_date isn't in the past
    # but an hour in the future
    mocker.patch(
        'atmo.clusters.provisioners.ClusterProvisioner.info',
        return_value={
            'creation_datetime': timezone.now(),
            'ready_datetime': None,
            'end_datetime': None,
            'state': Cluster.STATUS_TERMINATED,
            'state_change_reason_code': None,
            'state_change_reason_message': None,
            'public_dns': 'master.public.dns.name',
        },
    )
    spark_job_with_run = spark_job_with_run_factory(
        start_date=one_hour_ahead,
        run__status=Cluster.STATUS_TERMINATED,
    )
    mocker.spy(tasks.run_job, 'unschedule_and_expire')
    schedule_delete = mocker.patch(
        'atmo.jobs.schedules.SparkJobSchedule.delete'
    )
    expire = mocker.patch(
        'atmo.jobs.models.SparkJob.expire'
    )
    assert spark_job_with_run.has_finished
    assert schedule_delete.call_count == 0

    tasks.run_job(spark_job_with_run.pk)

    assert tasks.run_job.unschedule_and_expire.call_count == 1
    assert schedule_delete.call_count == 1
    assert expire.call_count == 1


def test_run_job_timed_out_job(mocker, now, one_hour_ahead,
                               spark_job_with_run_factory):
    # create a job with a run that started two hours ago but is only allowed
    # to run for an hour, so timing out
    spark_job_with_run = spark_job_with_run_factory(
        start_date=one_hour_ahead,
        job_timeout=1,
        run__status=Cluster.STATUS_WAITING,
        run__scheduled_at=now - timedelta(hours=2),
    )
    mocker.spy(tasks.run_job, 'terminate_and_notify')
    mocker.patch(
        'atmo.clusters.provisioners.ClusterProvisioner.info',
        return_value={
            'creation_datetime': now,
            'ready_datetime': None,
            'end_datetime': None,
            'state': Cluster.STATUS_WAITING,
            'public_dns': None,
        },
    )
    terminate = mocker.patch(
        'atmo.jobs.models.SparkJob.terminate'
    )
    assert not spark_job_with_run.has_finished
    assert spark_job_with_run.has_timed_out
    assert terminate.call_count == 0

    tasks.run_job(spark_job_with_run.pk)
    assert tasks.run_job.terminate_and_notify.call_count == 1
    assert terminate.call_count == 1


def test_run_job_dangling_job(mocker, now, one_hour_ago, one_hour_ahead,
                              spark_job_with_run_factory):
    # create a job with a run that started one hour ago and is allowed
    # to run for two hours, so it's not timing out, but it's not quite
    # healthy, too
    spark_job_with_run = spark_job_with_run_factory(
        start_date=one_hour_ahead,
        job_timeout=2,
        run__status=Cluster.STATUS_WAITING,
        run__scheduled_at=one_hour_ago,
    )
    mocker.spy(tasks.run_job, 'terminate_and_notify')
    mocker.patch(
        'atmo.clusters.provisioners.ClusterProvisioner.info',
        return_value={
            'creation_datetime': now,
            'ready_datetime': None,
            'end_datetime': None,
            'state': Cluster.STATUS_WAITING,
            'public_dns': None,
        },
    )
    terminate = mocker.patch(
        'atmo.jobs.models.SparkJob.terminate'
    )
    assert not spark_job_with_run.has_finished
    assert not spark_job_with_run.has_timed_out
    assert terminate.call_count == 0

    # tries running again
    with pytest.raises(Retry):
        tasks.run_job(spark_job_with_run.pk)

    assert tasks.run_job.terminate_and_notify.call_count == 0
    assert terminate.call_count == 0


def test_expire_jobs(mocker, one_hour_ago, spark_job_factory):
    spark_job = spark_job_factory(end_date=one_hour_ago)
    # manually adding the job to the schedule since we do a check
    # in the post_save signal handler for the end_date
    spark_job.schedule.add()
    mocker.spy(schedules.SparkJobSchedule, 'delete')
    result = tasks.expire_jobs()
    # 2 since 1 is called as part of the expire call and one
    # by the save call
    assert spark_job.schedule.delete.call_count == 2
    assert result == [[spark_job.identifier, spark_job.pk]]


def test_dont_expire_jobs(mocker, one_hour_ahead, spark_job_factory):
    spark_job = spark_job_factory(end_date=one_hour_ahead)
    mocker.spy(schedules.SparkJobSchedule, 'delete')
    result = tasks.expire_jobs()
    assert spark_job.schedule.delete.call_count == 0
    assert result == []


def test_expire_and_no_schedule_delete(mocker, one_hour_ago, spark_job_factory):
    # adding one Spark job to the schedule
    spark_job1 = spark_job_factory(end_date=one_hour_ago)
    spark_job1.schedule.add()

    # the other we don't add to make sure the logging isn't triggered
    spark_job2 = spark_job_factory(end_date=one_hour_ago)

    mocker.spy(schedules.SparkJobSchedule, 'delete')
    result = tasks.expire_jobs()
    # 4 since 1 is called as part of the expire call and one
    # by the save call, x 2 jobs to expire
    assert schedules.SparkJobSchedule.delete.call_count == 4
    assert sorted(result) == sorted([
        [spark_job1.identifier, spark_job1.pk],
        [spark_job2.identifier, spark_job2.pk],
    ])


@freeze_time('2016-04-05 13:25:47')
@pytest.mark.usefixtures('transactional_db')
def test_send_run_alert_mails(client, mailoutbox, mocker, spark_job,
                              sparkjob_provisioner_mocks):
    mocker.patch(
        'atmo.clusters.provisioners.ClusterProvisioner.info',
        return_value={
            'creation_datetime': timezone.now(),
            'ready_datetime': None,
            'end_datetime': None,
            'state': Cluster.STATUS_TERMINATED_WITH_ERRORS,
            'state_change_reason_code': Cluster.STATE_CHANGE_REASON_BOOTSTRAP_FAILURE,
            'state_change_reason_message': 'Bootstrapping steps failed.',
            'public_dns': None,
        },
    )
    spark_job.run()
    assert spark_job.latest_run.alerts.exists()
    assert len(mailoutbox) == 0
    tasks.send_run_alert_mails()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == (
        '%sRunning Spark job %s failed' %
        (settings.EMAIL_SUBJECT_PREFIX, spark_job.identifier)
    )

    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(message.cc) == [settings.DEFAULT_FROM_EMAIL]
    assert list(message.to) == [spark_job.created_by.email]


def test_update_jobs_statuses_empty(mocker, now, user):
    result = tasks.update_jobs_statuses()
    assert result == []


def test_update_jobs_statuses_full(mocker, now, user,
                                   spark_job_factory,
                                   spark_job_run_factory):
    spark_job1 = spark_job_factory.create(
        start_date=now - timedelta(days=1),
        created_by=user,
    )
    spark_job1_run = spark_job_run_factory.create(
        spark_job=spark_job1,
        status=Cluster.STATUS_RUNNING,
    )
    # setting created_at explicitly here since factoryboy isn't handling
    # auto_now fields such as created_at nicely, same for the other runs below
    spark_job1_run.created_at = spark_job1.start_date
    spark_job1_run.save()

    spark_job2 = spark_job_factory.create(
        start_date=now - timedelta(days=2),
        created_by=user,
    )
    spark_job2_run = spark_job_run_factory.create(
        spark_job=spark_job2,
        status=Cluster.STATUS_RUNNING,
    )
    spark_job2_run.created_at = spark_job2.start_date
    spark_job2_run.save()

    spark_job3 = spark_job_factory.create(
        start_date=now - timedelta(days=3),
        created_by=user,
    )
    spark_job3_run1 = spark_job_run_factory.create(
        spark_job=spark_job3,
        status=Cluster.STATUS_RUNNING,
    )
    spark_job3_run2 = spark_job_run_factory.create(
        spark_job=spark_job3,
        status=Cluster.STATUS_RUNNING,
    )
    spark_job3_run1.created_at = spark_job3.start_date
    spark_job3_run1.save()
    spark_job3_run2.created_at = spark_job3.start_date + timedelta(hours=1)
    spark_job3_run2.save()

    cluster_provisioner_list = mocker.patch(
        'atmo.clusters.provisioners.ClusterProvisioner.list',
        return_value=[
            {
                'jobflow_id': spark_job1_run.jobflow_id,
                'state': spark_job1_run.status,
                'creation_datetime': spark_job1.start_date,
                'ready_datetime': None,
                'end_datetime': None,
                'state_change_reason_code': '',
                'state_change_reason_message': '',
            },
            {
                'jobflow_id': spark_job2_run.jobflow_id,
                'state': spark_job2_run.status,
                'creation_datetime': spark_job2.start_date,
                'ready_datetime': None,
                'end_datetime': None,
                'state_change_reason_code': '',
                'state_change_reason_message': '',
            },
            {
                'jobflow_id': spark_job3_run1.jobflow_id,
                'state': spark_job3_run1.status,
                'creation_datetime': spark_job3.start_date,
                'ready_datetime': None,
                'end_datetime': None,
                'state_change_reason_code': '',
                'state_change_reason_message': '',
            },
            {
                'jobflow_id': spark_job3_run2.jobflow_id,
                'state': spark_job3_run2.status,
                'creation_datetime': spark_job3.start_date,
                'ready_datetime': None,
                'end_datetime': None,
                'state_change_reason_code': '',
                'state_change_reason_message': '',
            },
            # the cluster that should be ignored
            {
                'jobflow_id': 'j-some-other-id',
                'state': Cluster.STATUS_RUNNING,
                'creation_datetime': now - timedelta(days=10),
                'ready_datetime': None,
                'end_datetime': None,
                'state_change_reason_code': '',
                'state_change_reason_message': '',
            },
        ]
    )
    spark_job_run_sync = mocker.patch(
        'atmo.jobs.models.SparkJobRun.sync',
    )
    result = tasks.update_jobs_statuses()
    cluster_provisioner_list.assert_called_once_with(
        created_after=(
            now - timedelta(days=3)
        ).replace(hour=0, minute=0, second=0)  # we test a "day" datetimes query
    )
    # only four of five Spark job runs are updated
    assert spark_job_run_sync.call_count == 4
    assert result == [
        [spark_job1.identifier, spark_job1_run.pk],
        [spark_job2.identifier, spark_job2_run.pk],
        [spark_job3.identifier, spark_job3_run1.pk],
        [spark_job3.identifier, spark_job3_run2.pk],
    ]


def test_send_expired_mails(mailoutbox, mocker, now, spark_job):
    spark_job.expired_date = now
    spark_job.save()
    assert len(mailoutbox) == 0
    tasks.send_expired_mails()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == (
        '%sSpark job %s expired' %
        (settings.EMAIL_SUBJECT_PREFIX, spark_job.identifier)
    )
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(message.cc) == [settings.DEFAULT_FROM_EMAIL]
    assert list(message.to) == [spark_job.created_by.email]
    spark_job.refresh_from_db()


def test_metric_sparkjob_emr_version(spark_job, sparkjob_provisioner_mocks):
    spark_job.run()
    assert (Metric.objects.get(key='sparkjob-emr-version').data ==
            {'version': spark_job.emr_release.version})
