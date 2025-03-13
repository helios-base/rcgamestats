#!/bin/sh

cd `dirname $0`

echo "Reset hosts file"
sort -u all_hosts.tmpl > all_hosts

for host in `cat all_hosts`; do
    echo "Running client on $host"
    ssh $host "./rcgamestats/client/run.sh"
    echo "Done"
done

rm all_hosts
