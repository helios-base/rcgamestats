#!/bin/sh

# This script copies the client files to the remote hosts

cd `dirname $0`
. "./config"

if [ -z $1 ]; then
    echo "Usage: $0 <host>"
    exit 1
fi

host=$1
echo "=========="
echo "Copying client to $host"
rsync -auzv ~/local/ $host:local/
rsync -auzv ~/.rcssserver/ $host:.rcssserver/
rsync -auzv ../client/ $host:${REMOTE_CLIENT_DIR}/
echo "==="
echo "Initializing virtual environment on $host"
ssh $host "${REMOTE_CLIENT_DIR}/init_venv.sh"
echo "Done"
