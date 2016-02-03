from __future__ import unicode_literals

try:
  basestring
except NameError:
  basestring = str

from flask import Flask, Response


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


app = DynDnsFlask('route53_dyndns')


import route53_dyndns.views  # noqa
