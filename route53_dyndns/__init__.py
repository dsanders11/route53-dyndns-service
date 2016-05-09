try:
    from route53_dyndns.app import app  # noqa
except ImportError:
    pass  # Allow setup to grab the version even if Flask not installed
except:
    pass  # Allow testing to run even if no configuration is present


__version__ = "0.0.1dev"
