""" Backend functionality for communicating with Route 53 and updating DNS """

import boto3


class Route53Exception(Exception):
    pass


def get_client():
    """ Helper function to get an authenticated Route 53 client """

    return boto3.client('route53')


def find_resource_record(record_name, client=None):
    """ Find a DNS resource record on Route 53 """

    if not client:
        client = get_client()

    if not record_name:
        raise ValueError("Need a record name")

    try:
        response = client.list_resource_record_sets(
            HostedZoneId='string',
            StartRecordName=record_name,
            MaxItems='1'
        )
    except Exception as e:
        # TODO - Log the error
        raise Route53Exception(e)

    # We don't ever expect to get truncated results since we are looking up a
    # single record by name. TBD: This may fail if record types can share names
    assert not response['IsTruncated'], "Expected single record"
    assert len(response['ResourceRecordSets']) == 1, "Expected single record"

    response = response['ResourceRecordSets'][0]


def update_resource_record(resource_record, value, client=None):
    """ Update a resource record on Route 53 with a new value """

    if not client:
        client = get_client()

    record_name = resource_record['Name']
    record_type = resource_record['Type']
    set_identifier = resource_record['SetIdentifier']
    current_value = resource_record['ResourceRecords']['Value']

    if value == current_value:
        return True  # Nothing to do, it is already up-to-date

    try:
        client.change_resource_record_sets(
            HostedZoneId='string',
            ChangeBatch={
                'Comment': "Updating DNS record via route53_dyndns",
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': record_name,
                            'Type': record_type,
                            'SetIdentifier': set_identifier,
                            'ResourceRecords': [
                                {
                                    'Value': value
                                },
                            ],
                        }
                    },
                ]
            }
        )
    except Exception as e:
        # TODO - Log the error
        raise Route53Exception(e)

    return True
