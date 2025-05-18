#!/bin/sh

sudo -n cpufreq-set --help > /dev/null 2>&1
if [ $? -ne 0 ] ; then
  echo "cpufreq-set cannot be executed without password."
  exit 1
fi

NUM=`nproc --all`

i=0
while [ $i -lt $NUM ] ; do
  sudo cpufreq-set -c $i -g $@
  i=`expr $i + 1`
done
