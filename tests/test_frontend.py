from __future__ import unicode_literals

from base64 import b64encode
import unittest

from flask import Response

from route53_dyndns import app, route53, views

from mock import Mock, patch


class FrontendTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def make_auth_header(self, username, password):
        value = b64encode(bytes("{0}:{1}".format(username, password), 'ascii'))

        return {
            'Authorization': b'Basic ' + value
        }

    def assertResponseEqual(self, expected, rv):
        response = rv.get_data().decode('utf-8')

        return self.assertEqual(expected + '\r\n', response)

    def test_app_response(self):
        response = "Hello World!"

        # Check that a string response always has correct type and newline
        rv = app.make_response(response)
        self.assertEqual('text/plain', rv.headers['content-type'])
        self.assertResponseEqual(response, rv)

        # Check that a tuple response always has correct type and newline
        rv = app.make_response((response, 200, None))
        self.assertEqual('text/plain', rv.headers['content-type'])
        self.assertResponseEqual(response, rv)

        # Check that a response gets the correct type
        rv = app.make_response(Response(response, 200, None))
        self.assertEqual('text/plain', rv.headers['content-type'])

    def test_nic_update(self):
        URL = '/nic/update'

        # Check that the trailing slash on the URL is optional
        rv = self.app.get(URL + '/?hostname=foo.com')
        self.assertNotEqual(rv.status_code, 404)

        rv = self.app.get(URL + '?hostname=foo.com')
        self.assertNotEqual(rv.status_code, 404)

        # Test the authentication for the view
        with patch('route53_dyndns.views.verify_auth') as mocked:
            auth_url = URL + '?hostname=foo.com'

            # Test no authentication
            rv = self.app.get(auth_url)
            self.assertEqual(rv.status_code, 401)

            # Test incorrect authentication
            auth_header = self.make_auth_header('admin', 'admin')
            mocked.return_value = False
            rv = self.app.get(auth_url, headers=auth_header)
            self.assertEqual(rv.status_code, 403)

            # Test correct authentication
            auth_header = self.make_auth_header('admin', 'secret')
            mocked.return_value = True
            rv = self.app.get(auth_url, headers=auth_header)
            self.assertEqual(rv.status_code, 200)

        # Lock authentication to true
        views.verify_auth = Mock()
        views.verify_auth.return_value = True

        # Offline is an unsupported parameter
        rv = self.app.get(URL + '?offline=True', headers=auth_header)
        self.assertEqual(rv.status_code, 200)
        self.assertResponseEqual(views.NOT_SUPPORTED, rv)

        # Test no hostname
        rv = self.app.get(URL, headers=auth_header)
        self.assertEqual(rv.status_code, 200)
        self.assertResponseEqual(views.NO_HOST, rv)

        # Test a go wrong case when there's a Route 53 error
        with patch('route53_dyndns.route53.find_resource_record') as mocked:
            mocked.side_effect = route53.Route53Exception("Error")

            rv = self.app.get(URL + '?hostname=foo', headers=auth_header)
            self.assertResponseEqual(views.GENERAL_ERROR, rv)

        # Test hostname not found
        with patch('route53_dyndns.route53.find_resource_record') as mocked:
            mocked.return_value = None

            rv = self.app.get(URL + '?hostname=foo', headers=auth_header)
            self.assertResponseEqual(views.NO_HOST, rv)
