""" Setup for route53-dyndns-service """

from setuptools import setup, find_packages

from route53_dyndns import __version__


setup(
    name="route53-dyndns-service",
    version=__version__,
    description="Lightweight HTTP server that implements a dynamic DNS "
                "service compatible with routers which updates Route 53 DNS "
                "records.",
    long_description=open("README.rst", 'rb').read().decode('utf-8'),
    license="MIT",
    author="David Sanders",
    author_email="dsanders11@ucsbalum.com",
    url="https://github.com/dsanders11/route53-dyndns-service/",
    keywords="route53 ddns dyndns dns dynamic",
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "Flask >= 0.10",
        "boto3 >= 1.2.3"
    ],
    entry_points={
        "console_scripts": ["route53_dyndns=route53_dyndns.cmdline:main"],
    },
    test_suite="tests",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: Name Service (DNS)",
    ]
)
