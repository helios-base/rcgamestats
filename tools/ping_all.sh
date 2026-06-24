#!/bin/sh

cd `dirname $0`
. "./config"

sort -u $HOST_LIST > tmp_hosts

count=0
for i in `cat tmp_hosts`; do
    count=`expr $count + 1`
    if ! ping -c 1 -W 1 $i > /dev/null 2>&1; then
        echo "$count: $i \t... Unavailable"
    else
        echo "$count: $i \t... Ok"
    fi
done

rm tmp_hosts
