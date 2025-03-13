#!/bin/bashh

cd $(dirname $0)

source ~/.profile
source ~/.bashrc

if [ ! -d venv ]; then
    ./init_venv.sh
else
    source ./venv/bin/activate
fi

# run.py with nohup to keep running after logout
nohup python run.py > /dev/null 2>&1 &
