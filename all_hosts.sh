#!/bin/sh

all_hosts="all_hosts"

if [ $# -lt 1 ]; then
	echo "No command"
	exit 1
fi


echo "reset $all_hosts"
sort -u ${all_hosts}.tmpl > ${all_hosts}.command

for i in `cat ${all_hosts}.command`; do
	echo "=========="
	echo "$i: \"$*\""
	ssh $i "$*"
done

rm ${all_hosts}.command
