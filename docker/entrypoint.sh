#!/bin/bash

nginx &
jupyter notebook --port=8888 --debug --no-browser --ip=0.0.0.0 --allow-root &
uvicorn engin.main:app --host 0.0.0.0 --port 7777 --reload 
sleep infinity
