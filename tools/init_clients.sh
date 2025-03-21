#!/bin/sh

# This script copies the client files to the remote hosts

cd `dirname $0`
. "./config"

sort -u $HOST_LIST > tmp_hosts

for host in `cat tmp_hosts`; do
    ./init_one.sh $host
done

