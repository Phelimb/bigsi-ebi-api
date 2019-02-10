FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN apt-get update -y

RUN mkdir /bigsi-aggregator
WORKDIR /bigsi-aggregator
ADD . /bigsi-aggregator/

RUN pip install -r requirements.txt
RUN pip install uWSGI==2.0.18
EXPOSE 8001

CMD uwsgi  --harakiri 300 --socket-timeout 300 --single-interpreter  --enable-threads --socket :8001 --buffer-size=65535  --manage-script-name --mount bigsi_aggregator=bigsi_aggregator:app

