#!/bin/bash

# local testing
uvicorn main:app --host 0.0.0.0 --port 5800

# dev server testing
# nohup gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5800 main:app > log.txt 2>&1 &
