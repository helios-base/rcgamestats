#!/bin/sh

if [ $# -ne 4 ]; then
	echo "Usage:"
	echo "  $0 <group name> <opponent name> <match number>"
	exit 1
fi

logtime=`date "+%Y%m%d-%H%M%S"`

hostname=`hostname`
path=`dirname $0`

left_name=$1
right_name=$2
log_dir=$3
log_name=$4
teamlist="$path/teamlist.csv"

echo "run match: $left_name vs $right_name"

left_info=`grep "^${left_name}," $teamlist`
if [ -z $left_info ]; then
	echo "[$logtime] @$hostname team [$left_name] not available."
	exit 1
fi

right_info=`grep "^${right_name}," $teamlist`
if [ -z $right_info ]; then
	echo "[$logtime] @$hostname team [$right_name] not available."
	exit 1
fi

echo "left_info=$left_info"
echo "right_info=$right_info"

left_path=`echo $left_info | cut -d , -f 3`
if [ ! -d $left_path ]; then
	echo "[$logtime] @$hostname run_match: No path for $left_name"
	exit 1
fi

right_path=`echo $right_info | cut -d , -f 3`
if [ ! -d $right_path ]; then
	echo "[$logtime] @$hostname run_match: No path for $right_name"
	exit 1
fi

left_synch_mode=`echo $left_info | cut -d , -f 2`
right_synch_mode=`echo $right_info | cut -d , -f 2`
sync_mode=false
if [ $left_synch_mode = "true" -a $right_synch_mode = "true" ]; then
	synch_mode=true
fi

team_l_start=$left_path/start.sh
team_r_start=$right_path/start.sh

if [ ! -x $team_l_start ]; then
	echo "[$logtime] @$hostname remote_run_match: left team start script not found'"
	exit 1
fi

if [ ! -x $team_r_start ]; then
	echo "[$logtime] @$hostname remote_run_match: start.sh not found '$opponent_path/start.sh'"
	exit 1
fi

if [ ! -d $log_dir ]; then
	mkdir $log_dir
fi


#$path/cpufreq-set-all.sh performance

opt="server::game_logging = true server::text_logging = true"
#opt="$opt server::game_log_dated = true server::text_log_dated = true"
opt="$opt server::game_log_dated = true server::text_log_dated = false"
#opt="$opt server::game_log_fixed = false server::text_log_fixed = false"
opt="$opt server::game_log_fixed = true server::text_log_fixed = true"
opt="$opt server::game_log_fixed_name = '$log_name' server::text_log_fixed_name = '$log_name'"
opt="$opt server::game_log_compression = 9 server::text_log_compression = 9"
opt="$opt server::game_log_dir = '$log_dir' server::text_log_dir = '$log_dir'"
opt="$opt server::log_date_format = '%Y%m%d%H%M%S-'"
opt="$opt server::nr_normal_halfs = 2 server::nr_extra_halfs = 0 server::penalty_shoot_outs = false"
opt="$opt server::half_time = 1 server::extra_half_time = 100"
opt="$opt server::synch_mode = $synch_mode"
opt="$opt server::auto_mode = true"
opt="$opt server::team_l_start = '$team_l_start'"
opt="$opt server::team_r_start = '$team_r_start'"
opt="$opt CSVSaver::save = true CSVSaver::filename = '${log_name}.csv'"
#opt="$opt server::fixed_teamname_l = 'L' server::fixed_teamname_r = 'R'"

echo "[$logtime] @$hostname left=$left_name right=$right_name synch_mode=$synch_mode"
#echo $opt

start_epochtime=`date "+%s"`

$HOME/local/bin/rcssserver $opt 1> stdout.log 2> stderr.log

#sleep 2
sleep 1

end_epochtime=`date "+%s"`
elapsed_sec=`expr $end_epochtime - $start_epochtime`
elapsed_minutes=`expr \( $end_epochtime - $start_epochtime \) / 60`
elapsed_seconds=`expr \( $end_epochtime - $start_epochtime \) % 60`
printf "@%s match=[%d] elapsed %d:%02d\n" $hostname $match_number $elapsed_minutes $elapsed_seconds

#
# kill team scripts
#
$left_path/kill >/dev/null 2>&1
$right_path/kill >/dev/null 2>&1

#
# analyze log file???
#

#
# copy logs & result to server
#

mv ${log_name}.csv $log_dir

echo "[`date "+%Y%m%d-%H%M%S"`] @$hostname compressing debug log files..."

debug_log_dir="${log_name}"
mkdir -p $debug_log_dir
mv stdout.log stderr.log ${debug_log_dir}

if [ -e /tmp/HELIOS*-1.ocl ]; then
#	sleep 3.5
	mv /tmp/HELIOS*.ocl ${debug_log_dir}
else
	echo "[$logtime] @$hostname ocl not found"
fi

sleep 0.1
tar czf ${log_name}.tar.gz ${debug_log_dir}/*
rm -rf ${debug_log_dir}

mv ${log_name}.tar.gz $log_dir

echo "[`date "+%Y%m%d-%H%M%S"`] @$hostname sending log & result files to $server"


#$path/cpufreq-set-all.sh powersave


#
# add the result to the queued csv
#
#ssh $server "~/rcgamestats2/scripts/server_add_result.sh $group_name $opponent_name $match_number $hostname ${log_name}.csv"

#
# add this host to available-hosts on the server
#
#ssh $server "~/rcgamestats2/scripts/server_append_host.sh $hostname $match_number"

#
# save result to the spreadshet
#
#ssh -f $server "~/rcgamestats2/scripts/server_save_result.sh $group_name $opponent_name $match_number $hostname ${log_name}.csv"
