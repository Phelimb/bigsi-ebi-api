FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN apt-get update -y
RUN apt-get install curl -y

RUN mkdir /bigsi-aggregator
WORKDIR /bigsi-aggregator
ADD . /bigsi-aggregator/

RUN pip install -r requirements.txt
RUN pip install uWSGI==2.0.18
EXPOSE 80

CMD uwsgi --http :80 --harakiri 300  --buffer-size=65535 --protocol=http -w wsgi

