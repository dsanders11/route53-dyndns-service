from datetime import datetime
import unittest

from route53_dyndns.route53 import find_resource_record, update_resource_record


class MockRoute53Client(object):
    def list_resource_record_sets(self, *args, HostedZoneId=None,
                                  StartRecordName=None, MaxItems=None):
        assert len(args) == 0
        assert HostedZoneId
        assert StartRecordName
        assert MaxItems

        return {
            'ResourceRecordSets': [
                {
                    'Name': StartRecordName,
                    'Type': 'A',
                    'SetIdentifier': 'string',
                    'Region': 'us-east-1',
                    'TTL': 123,
                    'ResourceRecords': [
                        {
                            'Value': 'string'
                        },
                    ],
                },
            ],
            'IsTruncated': False,
            'MaxItems': MaxItems
        }

    def change_resource_record_sets(self, *args, HostedZoneId=None,
                                    ChangeBatch=None):
        assert len(args) == 0
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

        with self.assertRaises(ValueError):
            find_resource_record(None, client=client)

        with self.assertRaises(ValueError):
            find_resource_record('', client=client)

        resource_record = find_resource_record("www.google.com", client=client)

        self.assertEqual(resource_record['Name'], "www.google.com")

    def test_update_resource_record(self):
        """ Test update_resource_record functionality """

        client = MockRoute53Client()

        value = '127.0.0.1'
        resource_record = {
            'Name': 'www.google.com',
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

        updated = update_resource_record(resource_record, value, client=client)
        self.assertTrue(updated)
