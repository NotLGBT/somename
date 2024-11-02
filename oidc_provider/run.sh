#!/bin/bash

host=$1
port=$2

if [ -z "$host" ] || [ -z "$port" ]
then
    echo "Please provide host name and port as ./run.sh 0.0.0.0 5001"
    exit 1
fi

FLASK_APP=run.py FLASK_DEBUG=1 flask run --host=$host --port=$port