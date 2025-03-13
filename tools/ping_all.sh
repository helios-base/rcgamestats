#!/bin/sh

cd `dirname $0`

sort -u all_hosts.tmpl > all_hosts

count=0
for host in `cat all_hosts`; do
    count=`expr $count + 1`
    if ! ping -c 1 -W 1 $i > /dev/null 2>&1; then
        echo "$count: $i ... Unavailable"
    else
        echo "$count: $i ... Ok"
    fi
done

rm all_hosts
