#!/bin/bash

if ! grep -q "export PATH=\$HOME/rcss/tools/loganalyzer3:\$PATH" ~/.bashrc; then
    echo export PATH=\$HOME/rcss/tools/loganalyzer3:\$PATH >> ~/.bashrc
fi
source ~/.bashrc

cd $(dirname $0)

if [ ! -d venv ]; then
    echo "@${host} No venv found. Create it first."
    exit 1
fi

source ./venv/bin/activate
if [ $? -ne 0 ]; then
    echo "@${host} Failed to activate venv."
    exit 1
fi

cd ~/rcss/tools/loganalyzer3
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "@${host} Failed to install requirements."
    exit 1
fi

echo "@${host} Build loganalyzer3"
./build.sh
if [ $? -ne 0 ]; then
    echo "@${host} Failed to build loganalyzer3."
    exit 1
fi
echo "@${host} Setup loganalyzer3 completed."