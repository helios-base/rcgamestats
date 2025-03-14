#!/bin/bash

cd $(dirname $0)

source ~/.profile
source ~/.bashrc

host=`hostname`

if [ ! -d venv ]; then
    echo "@${host} No venv found. Create it first."
    exit 1
fi

source ./venv/bin/activate
if [ $? -ne 0 ]; then
    echo "@${host} Failed to activate venv."
    exit 1
fi

# run.py with nohup to keep running after logout
echo "@${host} Running client"
nohup python run.py > /dev/null 2>&1 &
