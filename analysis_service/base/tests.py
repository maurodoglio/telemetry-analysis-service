from django.core.urlresolvers import reverse
from django.test import TestCase


class HomeTests(TestCase):

    def test_login(self):
        response = self.client.get(reverse('login'))
        assert b'csrfmiddlewaretoken' in response.content


class TestContribute(TestCase):

    def test_contribute_json(self):
        response = self.client.get('/contribute.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
