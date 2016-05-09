from __future__ import unicode_literals

from base64 import b64encode
import unittest

from flask import Response

from route53_dyndns import app, route53, views

from mock import patch

from .helpers import new_resource_record


class FrontendTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.url = '/nic/update'

    def make_auth_header(self, username, password):
        value = b64encode("{0}:{1}".format(username, password).encode('ascii'))

        return {
            'Authorization': b'Basic ' + value
        }

    def get_with_auth(self, url, username='admin', password='admin', **kwargs):
        auth_header = self.make_auth_header(username, password)

        if 'environ_base' in kwargs:
            kwargs['environ_base'].setdefault('HTTP_USER_AGENT', "Client")
        else:
            kwargs['environ_base'] = {'HTTP_USER_AGENT': "Client"}

        return self.app.get(url, headers=auth_header, **kwargs)

    def assertResponseEqual(self, expected, rv):
        response = rv.get_data().decode('utf-8')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(expected + '\r\n', response)

    def test_app_sanity_check_config(self):
        # Test required settings
        for setting in ('USERNAME', 'PASSWORD'):
            with patch.dict(app.config):
                app.config.pop(setting)

                with self.assertRaises(RuntimeError):
                    app.sanity_check_config()

        # Test optional settings
        for setting in ('BAD_USER_AGENTS',):
            with patch.dict(app.config):
                app.config.pop(setting)
                self.assertFalse(setting in app.config)

                app.sanity_check_config()

                self.assertTrue(setting in app.config)

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

    def test_verify_auth(self):
        verified = views.verify_auth('admin', 'admin')
        self.assertFalse(verified)

        verified = views.verify_auth('admin', 'secret')
        self.assertTrue(verified)

    def test_nic_update_http(self):
        # Check that the trailing slash on the URL is optional
        rv = self.app.get(self.url + '/?hostname=foo.com')
        self.assertNotEqual(rv.status_code, 404)

        rv = self.app.get(self.url + '?hostname=foo.com')
        self.assertNotEqual(rv.status_code, 404)

        # Test the authentication logic for a view
        with patch('route53_dyndns.views.verify_auth') as mocked:
            auth_url = '/test_auth'

            @app.route(auth_url)
            @views.api_auth
            def test_view():
                return 'OK'

            # Test no authentication
            rv = self.app.get(auth_url)
            self.assertEqual(rv.status_code, 401)

            # Test incorrect authentication
            mocked.return_value = False
            rv = self.get_with_auth(auth_url)
            self.assertEqual(rv.status_code, 403)

            # Test correct authentication
            mocked.return_value = True
            rv = self.get_with_auth(auth_url)
            self.assertEqual(rv.status_code, 200)

    @patch('route53_dyndns.views.verify_auth', **{'method.return_value': True})
    def test_nic_update_parameters(self, mocked_auth):
        # Offline is an unsupported parameter
        rv = self.get_with_auth(self.url + '?offline=True')
        self.assertResponseEqual(views.NOT_SUPPORTED, rv)

    @patch('route53_dyndns.views.verify_auth', **{'method.return_value': True})
    def test_nic_update_user_agent(self, mocked_auth):
        # Test no user agent
        rv = self.get_with_auth(self.url, environ_base={'HTTP_USER_AGENT': ''})
        self.assertResponseEqual(views.BAD_USER_AGENT, rv)

        # Test no bad user agents
        with patch.dict(app.config, {'BAD_USER_AGENTS': []}):
            rv = self.get_with_auth(self.url,
                                    environ_base={'HTTP_USER_AGENT': "foobar"})
            self.assertResponseEqual(views.NO_HOST, rv)

        # Test bad user agent
        with patch.dict(app.config, {'BAD_USER_AGENTS': ["foobar"]}):
            rv = self.get_with_auth(self.url + '?hostname=foo',
                                    environ_base={'HTTP_USER_AGENT': "foobar"})
            self.assertResponseEqual(views.BAD_USER_AGENT, rv)

    @patch('route53_dyndns.views.verify_auth', **{'method.return_value': True})
    def test_nic_update_hostname(self, mocked_auth):
        # Test no hostname
        rv = self.get_with_auth(self.url)
        self.assertResponseEqual(views.NO_HOST, rv)

        # Test a go wrong case when there's a Route 53 error
        with patch('route53_dyndns.route53.find_resource_record') as mocked:
            mocked.side_effect = route53.Route53Exception("Error")

            rv = self.get_with_auth(self.url + '?hostname=foo')
            self.assertResponseEqual(views.GENERAL_ERROR, rv)

        # Test hostname not found
        with patch('route53_dyndns.route53.find_resource_record') as mocked:
            mocked.return_value = None

            rv = self.get_with_auth(self.url + '?hostname=foo')
            self.assertResponseEqual(views.NO_HOST, rv)

    @patch('route53_dyndns.route53.find_resource_record')
    @patch('route53_dyndns.views.verify_auth', **{'method.return_value': True})
    def test_nic_update_record_exists(self, mocked_auth, mocked_find_record):
        hostname = "www.google.com"
        value = "10.1.10.1"
        new_value = "192.168.1.1"
        mocked_find_record.return_value = new_resource_record(hostname, value)

        # Test IP hasn't changed
        url = self.url + '?hostname=' + hostname + '&myip=' + value
        rv = self.get_with_auth(url)
        self.assertResponseEqual(views.NO_CHANGE % value, rv)

        # Test IP hasn't changed, implicit IP from request
        rv = self.get_with_auth(self.url + '?hostname=' + hostname,
                                environ_base={'REMOTE_ADDR': value})
        self.assertResponseEqual(views.NO_CHANGE % value, rv)

        # Test go wrong case when there's an exception
        with patch('route53_dyndns.route53.update_resource_record') as mocked:
            mocked.side_effect = route53.Route53Exception("Error")

            url = self.url + '?hostname=' + hostname + '&myip=' + new_value
            rv = self.get_with_auth(url)
            self.assertResponseEqual(views.GENERAL_ERROR, rv)

        # Test go wrong case when there's an expected failure
        with patch('route53_dyndns.route53.update_resource_record') as mocked:
            mocked.return_value = False

            url = self.url + '?hostname=' + hostname + '&myip=' + new_value
            rv = self.get_with_auth(url)
            self.assertResponseEqual(views.GENERAL_ERROR, rv)

        with patch('route53_dyndns.route53.update_resource_record') as mocked:
            mocked.return_value = True

            # Go right case with explicit new IP
            url = self.url + '?hostname=' + hostname + '&myip=' + new_value
            rv = self.get_with_auth(url)
            self.assertResponseEqual(views.IP_CHANGED % new_value, rv)

            # Go right case with implict new IP from request
            url = self.url + '?hostname=' + hostname + '&myip=' + new_value
            rv = self.get_with_auth(url,
                                    environ_base={'REMOTE_ADDR': new_value})
            self.assertResponseEqual(views.IP_CHANGED % new_value, rv)
