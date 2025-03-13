#!/bin/sh

# This script runs a command on all hosts

cd `dirname $0`
. "./config"

if [ $# -lt 1 ]; then
	echo "No command"
	exit 1
fi

sort -u $HOSTS > tmp_hosts

for i in `cat tmp_hosts`; do
	echo "=========="
	echo "$i: \"$*\""
	ssh $i "$*"
done

rm tmp_hosts
