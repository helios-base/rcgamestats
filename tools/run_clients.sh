#!/bin/sh

cd `dirname $0`
. "./config"

sort -u $HOST_LIST > tmp_hosts

for host in `cat tmp_hosts`; do
    echo "Running client on $host"
    ssh $host "${REMOTE_CLIENT_DIR}/run.sh"
    echo "Done"
done

rm tmp_hosts
