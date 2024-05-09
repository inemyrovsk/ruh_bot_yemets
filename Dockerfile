FROM python:3.8.19-alpine3.19

RUN mkdir -p /srv/images

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./src /srv/src

WORKDIR /srv