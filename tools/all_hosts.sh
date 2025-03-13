#!/bin/sh

all_hosts="all_hosts"

if [ $# -lt 1 ]; then
	echo "No command"
	exit 1
fi

echo "Reset hosts file"
sort -u all_hosts.tmpl > all_hosts

for i in `cat all_hosts`; do
	echo "=========="
	echo "$i: \"$*\""
	ssh $i "$*"
done

rm all_hosts
