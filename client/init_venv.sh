#!/bin/sh

cd $(dirname $0)

if [ ! -d venv ]; then
    python3 -m venv venv
else
    echo "venv already exists."
fi

source ./venv/bin/activate
pip install -r requirements.txt
