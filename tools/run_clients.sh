#!/bin/sh

cd `dirname $0`
. "./config"

sort -u $HOST_LIST > tmp_hosts

for host in `cat tmp_hosts`; do
    echo "----"
    echo "Running client on $host"
    ssh $host "${REMOTE_CLIENT_DIR}/run.sh"
    sleep 0.1
    echo "->Done"
done

rm tmp_hosts
