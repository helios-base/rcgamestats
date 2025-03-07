#!/bin/sh

URL="http://127.0.0.1:5000"
KEY="xxxxxx"

# This script is used to upload the group only by specifying the group directory
# The group directory should be in the format of "YYYYMMDD-HHMMSS-left-right{-*}"

# check if the group directory is specified
if [ -z "$1" ]; then
    echo "Usage: $0 <group_dir>"
    exit 1
fi

dir_path="$1"

# check if the group directory exists
if [ ! -d "$dir_path" ]; then
    echo "Error: $dir_path is not a directory"
    exit 1
fi

group_name=$(basename "$dir_path")

# check the directory name format
teams=$(echo "$group_name" | sed -E 's/^[0-9]{8}-[0-9]{6}-([^-]+)-([^-]+)(-.*)?$/\1 \2/')

# exit if the directory name format is invalid
if [ "$teams" = "$group_name" ]; then
    echo "Error: Directory name format is invalid."
    exit 1
fi

# get the team names
left_team=$(echo "$teams" | awk '{print $1}')
right_team=$(echo "$teams" | awk '{print $2}')

echo "Left team: $left_team"
echo "Right team: $right_team"

opt=""
opt="$opt -u $URL"
opt="$opt -a $KEY"
opt="$opt -g $dir_path"
opt="$opt -n $group_name"
opt="$opt -l $left_team"
opt="$opt -r $right_team"

python submit.py $opt
