#!/bin/bash

WORKING_DIR="${PWD}/"
echo "DIR IS '$WORKING_DIR'"

cd $WORKING_DIR

if [ -f gunicorn.pid ];then
        echo "LUNGO is running"
else
        echo "NOT RUNNNING!"
fi
