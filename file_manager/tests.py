from django.test import TestCase

from .models import Connection


class ConnectionModelTests(TestCase):

    def test_connection_represent(self):
        connection = Connection(username='anna', host='34.56.78.39')
        self.assertEqual(
            str(connection), 'anna@34.56.78.39',
            'Wrong representation of Connection')
