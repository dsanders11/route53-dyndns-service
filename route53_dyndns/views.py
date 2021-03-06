""" HTTP API for updating dynamic DNS records """

from __future__ import unicode_literals

from functools import wraps

from flask import request

from route53_dyndns.app import app
from route53_dyndns import route53

AUTH_REALM = "Route 53 DNS Update API"

BAD_AUTH = 'badauth'
BAD_USER_AGENT = 'badagent'
IP_CHANGED = 'good %s'
NO_CHANGE = 'nochg %s'
NO_HOST = 'nohost'
NOT_SUPPORTED = '!donator'
GENERAL_ERROR = '911'


def verify_auth(username, password):
    """ Verify the HTTP Basic Auth credentials """

    config = app.config

    return username == config['USERNAME'] and password == config['PASSWORD']


def authenticate_response(forbidden=False):
    """ Generate an authenticate response for HTTP Basic Auth """

    headers = {
        'WWW-Authenticate': 'Basic realm="{}"'.format(AUTH_REALM)
    }

    return (BAD_AUTH, 403 if forbidden else 401, headers)


def api_auth(view):
    """ Decorator to add HTTP Basic Auth to a view """

    @wraps(view)
    def decorated(*args, **kwargs):
        auth = request.authorization

        if not auth:  # Auth is required at all times
            return authenticate_response()

        if not verify_auth(auth.username, auth.password):
            return authenticate_response(forbidden=True)

        return view(*args, **kwargs)

    return decorated


@app.route('/nic/update/', methods=['GET'])
@app.route('/nic/update', methods=['GET'])
@api_auth
def nic_update():
    """ Update a dynamic DNS record """

    if request.args.get('offline'):
        return NOT_SUPPORTED

    # Check for a user agent
    user_agent = request.user_agent.string

    if not user_agent:
        print("WTF")
    if not user_agent or user_agent in app.config['BAD_USER_AGENTS']:
        return BAD_USER_AGENT

    try:
        hostname = request.args.get('hostname')
        resource_record = route53.find_resource_record(hostname)
    except ValueError:
        return NO_HOST
    except:
        return GENERAL_ERROR

    if not resource_record:
        return NO_HOST

    # TODO - A sanity check of the value would be good, but good luck doing it
    #        easily in anything before Python 3.3+ which got 'ipaddress' module
    # TODO - Comma separated values should be allowed
    myip = request.args.get('myip', request.remote_addr)

    if myip == resource_record['ResourceRecords'][0]['Value']:
        return NO_CHANGE % myip

    try:
        if not route53.update_resource_record(resource_record, myip):
            return GENERAL_ERROR
    except:
        return GENERAL_ERROR

    return IP_CHANGED % myip
