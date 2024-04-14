FROM python:3.10-slim

RUN mkdir /app && mkdir /app/media && mkdir /app/src

RUN pip install --upgrade pip

COPY requirements.txt /app

RUN pip install -r /app/requirements.txt

COPY src /app/src

WORKDIR /app

