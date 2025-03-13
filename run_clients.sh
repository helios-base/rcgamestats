#!/bin/bash

REMOTE_HOSTS=(
  " sim01
    sim02
    sim03
    sim04
    sim05
    sim06
    sim07
    sim08
    sim09
    sim10
    "
)

for host in ${REMOTE_HOSTS[@]}; do
  ssh $host 'bash -s' < ./client/run.sh
done
