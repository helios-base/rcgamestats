#!/bin/sh

cd `dirname $0`
. "./config"

sort -u $HOST_LIST > tmp_hosts

for host in `cat tmp_hosts`; do
    echo "Stopping client on $host"
    ssh $host "touch ${REMOTE_CLIENT_DIR}/stop"
    echo "Done"
done
