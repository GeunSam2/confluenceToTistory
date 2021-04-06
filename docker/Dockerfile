FROM python:3.7

RUN pip install fastapi[all] \
pip install requestes \
pip install bs4

COPY engin /engin

WORKDIR /engin

expose 8000

ENTRYPOINT uvicorn main:app --reload
