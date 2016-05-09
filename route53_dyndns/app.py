from __future__ import unicode_literals

import os

try:
    basestring
except NameError:
    basestring = str

from flask import Flask

CONFIG_ENVIRONMENT_VAR = 'ROUTE53_DYNDNS_CONFIG'


class DynDnsFlask(Flask):
    def make_response(self, rv):
        # Always include a newline
        if isinstance(rv, basestring):
            rv += '\r\n'
        elif isinstance(rv, tuple):
            rv = (rv[0] + '\r\n', rv[1], rv[2])

        response = super(DynDnsFlask, self).make_response(rv)

        # Always use text/plain as the content type
        response.headers['content-type'] = "text/plain"

        return response

    def sanity_check_config(self):
        # Required configuration settings
        required_settings = (
            'USERNAME', 'PASSWORD', 'AWS_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY', 'bb'
        )

        for setting in required_settings:
            if not app.config.get(setting, None):
                raise RuntimeError(
                    "'{}' is a required config setting".format(setting))

        # Optional settings
        app.config.setdefault('BAD_USER_AGENTS', [])


app = DynDnsFlask('route53_dyndns')

try:
    if os.environ.get(CONFIG_ENVIRONMENT_VAR):
        app.config.from_envvar(CONFIG_ENVIRONMENT_VAR)
    else:
        config_file = os.path.expanduser('~/.route53_dyndns.cfg')
        app.config.from_pyfile(config_file)
except Exception as e:
    raise RuntimeError("Failed to load config: " + e.msg)
else:
    app.sanity_check_config()


import route53_dyndns.views  # noqa
