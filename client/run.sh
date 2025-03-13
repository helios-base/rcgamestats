#!/bin/bashh

cd $(dirname $0)

if [ ! -d venv ]; then
    ./init_venv.sh
else
    source ./venv/bin/activate
fi

# run.py を nohup 付きで起動
nohup python run.py > /dev/null 2>&1 &
