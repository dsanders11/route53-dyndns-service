def new_resource_record(name, value):
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
