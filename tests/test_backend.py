from datetime import datetime
import unittest

from route53_dyndns.route53 import (
    find_resource_record, Route53Exception, update_resource_record)

from mock import patch


class MockRoute53Client(object):
    def _resource_record(self, name, value):
        return {
            'Name': name,
            'Type': 'A',
            'SetIdentifier': 'string',
            'Region': 'us-east-1',
            'TTL': 123,
            'ResourceRecords': [
                {
                    'Value': value
                },
            ],
        }

    def _resource_records_response(self, name, max_items):
        return {
            'ResourceRecordSets': [
                self._resource_record(name, 'string')
            ],
            'IsTruncated': False,
            'MaxItems': max_items
        }

    def list_resource_record_sets(self, HostedZoneId=None,
                                  StartRecordName=None, MaxItems=None):
        assert HostedZoneId
        assert StartRecordName
        assert MaxItems

        return self._resource_records_response(StartRecordName, MaxItems)

    def change_resource_record_sets(self, HostedZoneId=None,
                                    ChangeBatch=None):
        assert HostedZoneId
        assert ChangeBatch

        return {
            'ChangeInfo': {
                'Id': 'string',
                'Status': 'PENDING',
                'SubmittedAt': datetime(2015, 1, 1),
                'Comment': ChangeBatch['Comment']
            }
        }


class BackendTestCase(unittest.TestCase):
    def test_find_resource_record(self):
        """ Test find_resource_record functionality """

        client = MockRoute53Client()
        hostname = "www.google.com"

        # Test some invalid inputs
        with self.assertRaises(ValueError):
            find_resource_record(None, client=client)

        with self.assertRaises(ValueError):
            find_resource_record('', client=client)

        # Go right case
        resource_record = find_resource_record(hostname, client=client)
        self.assertEqual(resource_record['Name'], hostname)

        # Test a go wrong case when there's a Route 53 error
        with patch.object(client, 'list_resource_record_sets') as mocked:
            mocked.side_effect = RuntimeError("Route 53 Error")

            with self.assertRaises(Route53Exception):
                find_resource_record(hostname, client=client)

        # Test a go wrong case where the returned result is truncated
        truncated_result = client._resource_records_response(hostname, 1)
        truncated_result['IsTruncated'] = True

        with patch.object(client, 'list_resource_record_sets') as mocked:
            mocked.return_value = truncated_result

            with self.assertRaises(AssertionError):
                find_resource_record(hostname, client=client)

        # Test a go wrong case where there are multiple resource record results
        multi_result = client._resource_records_response(hostname, 1)
        multi_result['ResourceRecordSets'] += client._resource_record(hostname,
                                                                      'whoops')

        with patch.object(client, 'list_resource_record_sets') as mocked:
            mocked.return_value = multi_result

            with self.assertRaises(AssertionError):
                find_resource_record(hostname, client=client)

    def test_update_resource_record(self):
        """ Test update_resource_record functionality """

        client = MockRoute53Client()
        hostname = "www.google.com"
        value = '127.0.0.1'
        record = client._resource_record(hostname, value)

        # Go right case where the value is the same as the in the record
        updated = update_resource_record(record, value, client=client)
        self.assertTrue(updated)

        # Go right case
        updated = update_resource_record(record, '192.168.1.1', client=client)
        self.assertTrue(updated)

        # Test a go wrong case when there's a Route 53 error
        with patch.object(client, 'change_resource_record_sets') as mocked:
            mocked.side_effect = RuntimeError("Route 53 Error")

            with self.assertRaises(Route53Exception):
                update_resource_record(record, '192.168.1.1', client=client)
