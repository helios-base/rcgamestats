#!/bin/bash

cd $(dirname $0)

host=`hostname`

if [ ! -d venv ]; then
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "@${host} Failed to create venv."
        exit 1
    fi
else
    echo "@${host} venv already exists."
fi

echo "@${host} Activating venv"
source ./venv/bin/activate
if [ $? -ne 0 ]; then
    echo "@${host} Failed to activate venv."
    exit 1
fi

echo "@${host} Installing requirements"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "@${host} Failed to install requirements."
    exit 1
fi
