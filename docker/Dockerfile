FROM python:3.7

RUN pip install fastapi[all] \
pip install requestes \
pip install bs4 \
pip install notebook

RUN apt-get update && \
apt-get install -y nginx

COPY engin /app
COPY ssl /source/certs
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh

WORKDIR /app

expose 8000

ENTRYPOINT /entrypoint.sh
