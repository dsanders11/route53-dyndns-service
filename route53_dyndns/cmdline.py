#!/usr/bin/env python

""" Command-line functionality for route53_dyndns """

import logging
import sys

from optparse import OptionParser, BadOptionError, AmbiguousOptionError

from route53_dyndns import __version__, app

logger = logging.getLogger(__name__)


def configure_logging(level=logging.INFO, logger=None):
    """ Configure logging for the command-line """

    if logger is None:  # pragma: no cover
        logger = logging.getLogger()

    handler = logging.StreamHandler(sys.stdout)

    logger.addHandler(handler)
    logger.setLevel(level)


def main(args=sys.argv[1:], parser=None):
    """ Main entry point for the route53_dyndns command-line script """

    usage = "%prog [options] [args]\n\n"
    version = "%prog " + __version__

    usage += "%prog is the HTTP dynamic DNS server for Route53"

    if parser is None:  # pragma: no cover
        parser = OptionParser(usage=usage, version=version,
                              add_help_option=False)
    parser.remove_option("--version")  # Remove standard version option

    parser.add_option("-h", "--help", dest="help", action="store_true",
                      help="Show help and exit")
    parser.add_option("-V", "--version", dest="version", action="store_true",
                      help="Show version and exit")

    (options, parsed_args) = parser.parse_args(args)

    # Check if we should print help or version number
    if not parsed_args or (parsed_args and len(parsed_args) == 0):
        if options.version:
            parser.print_version()
            sys.exit(0)
        elif options.help:
            parser.print_help()
            sys.exit(0)

    configure_logging()

    app.run(debug=True)
