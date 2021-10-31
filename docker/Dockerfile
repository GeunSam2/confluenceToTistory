FROM python:3.7

COPY docker /build
COPY engin /app

RUN pip install -r /build/requirements.txt

RUN apt-get update && \
apt-get install -y nginx

COPY nginx/default.conf /etc/nginx/conf.d/default.conf

RUN chmod 755 /build/entrypoint.sh

WORKDIR /app

EXPOSE 80

ENTRYPOINT ["/bin/bash", "-c", "/build/entrypoint.sh"]
