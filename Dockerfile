FROM python:3
MAINTAINER David Sanders <dsanders11@ucsbalum.com>

EXPOSE 5000

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app
RUN python setup.py install
