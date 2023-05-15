FROM --platform=linux/x86-64 python:3.8.3-slim-buster

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2

RUN pip install --no-cache-dir pandas

RUN python3 -m pip install -r requirements.txt --no-cache-dir


COPY . /app

CMD ["python","-u","main.py"]
