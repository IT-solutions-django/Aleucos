FROM python:3.10-slim 

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt 
RUN pip install -r requirements.txt 

RUN apt-get update \
    && apt-get -y install libpq-dev gcc netcat-openbsd postgresql-client 

COPY . . 

RUN chmod +x entrypoint.sh