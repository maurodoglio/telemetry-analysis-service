import io
import mock
from datetime import datetime, timedelta
from pytz import UTC
from django.test import TestCase
from django.contrib.auth.models import User
from analysis_service.base import models


class TestAuthentication(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user('john.smith', 'john@smith.com', 'hunter2')

    def test_that_login_page_is_csrf_protected(self):
        response = self.client.get('/login/')
        self.assertIn(b'csrfmiddlewaretoken', response.content)

    def test_that_login_works(self):
        self.assertTrue(self.client.login(username="john.smith", password="hunter2"))


class TestCreateCluster(TestCase):
    @mock.patch('analysis_service.base.util.provisioning.cluster_stop', return_value=None)
    @mock.patch('analysis_service.base.util.provisioning.cluster_start', return_value=u'12345')
    def setUp(self, cluster_start, cluster_stop):
        self.start_date = datetime.now().replace(tzinfo=UTC)
        self.test_user = User.objects.create_user('john.smith', 'john@smith.com', 'hunter2')
        self.client.force_login(self.test_user)

        # request that a new cluster be created
        self.response = self.client.post('/new-cluster/', {
            'identifier': 'test-cluster',
            'size': 5,
            'public_key': io.BytesIO('ssh-rsa AAAAB3'),
        }, follow=True)

        # delete the cluster
        self.cluster = models.Cluster.objects.get(jobflow_id=u'12345')
        self.cluster.delete()

        self.cluster_start = cluster_start
        self.cluster_stop = cluster_stop

    def test_that_request_succeeded(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.redirect_chain[-1], ('/', 302))

    def test_that_cluster_is_correctly_provisioned(self):
        self.assertEqual(self.cluster_start.call_count, 1)
        (user_email, identifier, size, public_key) = self.cluster_start.call_args[0]
        self.assertEqual(user_email, 'john@smith.com')
        self.assertEqual(identifier, 'test-cluster')
        self.assertEqual(size, 5)
        self.assertEqual(public_key, 'ssh-rsa AAAAB3')

    def test_that_the_model_was_created_correctly(self):
        self.assertEqual(self.cluster.identifier, 'test-cluster')
        self.assertEqual(self.cluster.size, 5)
        self.assertEqual(self.cluster.public_key, 'ssh-rsa AAAAB3')
        self.assertTrue(
            self.start_date <= self.cluster.start_date <= self.start_date + timedelta(seconds=10)
        )
        self.assertEqual(self.cluster.created_by, self.test_user)
        self.assertTrue(User.objects.filter(username='john.smith').exists())

    def test_that_deleting_the_cluster_kills_the_cluster(self):
        self.assertEqual(self.cluster_stop.call_count, 1)
        (jobflow_id,) = self.cluster_stop.call_args[0]
        self.assertEqual(jobflow_id, u'12345')


class TestEditCluster(TestCase):
    @mock.patch('analysis_service.base.util.provisioning.cluster_rename', return_value=None)
    def setUp(self, cluster_rename):
        self.start_date = datetime.now().replace(tzinfo=UTC)

        # create a test cluster to edit later
        self.test_user = User.objects.create_user('john.smith', 'john@smith.com', 'hunter2')
        self.cluster = models.Cluster()
        self.cluster.identifier = 'test-cluster'
        self.cluster.size = 5
        self.cluster.public_key = 'ssh-rsa AAAAB3'
        self.cluster.created_by = self.test_user
        self.cluster.jobflow_id = u'12345'
        self.cluster.save()

        # request that the test cluster be edited
        self.client.force_login(self.test_user)
        self.response = self.client.post('/edit-cluster/', {
            'cluster_id': self.cluster.id,
            'identifier': 'new-cluster-name',
        }, follow=True)

        self.cluster = models.Cluster.objects.get(jobflow_id=u'12345')

        self.cluster_rename = cluster_rename

    def test_that_request_succeeded(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.redirect_chain[-1], ('/', 302))

    def test_that_cluster_is_correctly_edited(self):
        self.assertEqual(self.cluster_rename.call_count, 1)
        (jobflow_id, new_identifier) = self.cluster_rename.call_args[0]
        self.assertEqual(jobflow_id, u'12345')
        self.assertEqual(new_identifier, 'new-cluster-name')

    def test_that_the_model_was_edited_correctly(self):
        self.assertEqual(self.cluster.identifier, 'new-cluster-name')
        self.assertEqual(self.cluster.size, 5)
        self.assertEqual(self.cluster.public_key, 'ssh-rsa AAAAB3')
        self.assertTrue(
            self.start_date <= self.cluster.start_date <= self.start_date + timedelta(seconds=10)
        )
        self.assertEqual(self.cluster.created_by, self.test_user)
        self.assertTrue(User.objects.filter(username='john.smith').exists())


class TestDeleteCluster(TestCase):
    @mock.patch('analysis_service.base.util.provisioning.cluster_stop', return_value=None)
    def setUp(self, cluster_stop):
        self.start_date = datetime.now().replace(tzinfo=UTC)

        # create a test cluster to edit later
        self.test_user = User.objects.create_user('john.smith', 'john@smith.com', 'hunter2')
        self.cluster = models.Cluster()
        self.cluster.identifier = 'test-cluster'
        self.cluster.size = 5
        self.cluster.public_key = 'ssh-rsa AAAAB3'
        self.cluster.created_by = self.test_user
        self.cluster.jobflow_id = u'12345'
        self.cluster.save()

        # request that the test cluster be edited
        self.client.force_login(self.test_user)
        self.response = self.client.post('/delete-cluster/', {
            'cluster_id': self.cluster.id,
            'identifier': 'new-cluster-name',
        }, follow=True)

        self.cluster_stop = cluster_stop

    def test_that_request_succeeded(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.redirect_chain[-1], ('/', 302))

    def test_that_cluster_is_correctly_deleted(self):
        self.assertEqual(self.cluster_stop.call_count, 1)
        (jobflow_id,) = self.cluster_stop.call_args[0]
        self.assertEqual(jobflow_id, u'12345')

    def test_that_the_model_was_deleted_correctly(self):
        self.assertFalse(models.Cluster.objects.filter(jobflow_id=u'12345').exists())
        self.assertTrue(User.objects.filter(username='john.smith').exists())
