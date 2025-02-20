#!/bin/sh

if [ $# -ne 5 ]; then
    echo "Usage:"
    echo "  $0 <left_team_path> <right_team_path> <synch_mode> <log_dir> <log_name>"
    exit 1
fi

logtime=`date "+%Y%m%d-%H%M%S"`
hostname=`hostname`
current_path=`dirname $0`

left_path=$1
right_path=$2
synch_mode=$3
log_dir=$4
log_name=$5

left_name=`basename $left_path`
right_name=`basename $right_path`

echo "[$logtime] run match: $left_name vs $right_name"

team_l_start=$left_path/start.sh
team_r_start=$right_path/start.sh

if [ ! -x $team_l_start ]; then
    echo "[$logtime] @$hostname run_match: left team start script not found"
    exit 1
fi

if [ ! -x $team_r_start ]; then
    echo "[$logtime] @$hostname run_match: right team start script not found"
    exit 1
fi

if [ ! -d $log_dir ]; then
    echo "[$logtime] @$hostname run_match: log directory not found"
    exit 1
fi

if [ -x $current_path/cpufreq_set_all.sh ]; then
    $current_path/cpufreq_set_all.sh performance
fi

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
#opt="$opt server::nr_normal_halfs = 1 server::nr_extra_halfs = 0 server::penalty_shoot_outs = false"
opt="$opt server::half_time = 300 server::extra_half_time = 100"
opt="$opt server::synch_mode = $synch_mode"
opt="$opt server::auto_mode = true"
opt="$opt server::team_l_start = '$team_l_start'"
opt="$opt server::team_r_start = '$team_r_start'"
opt="$opt CSVSaver::save = true CSVSaver::filename = '${log_name}.result.csv'"
#opt="$opt server::fixed_teamname_l = 'L' server::fixed_teamname_r = 'R'"

echo "[$logtime] @$hostname left=$left_name right=$right_name synch_mode=$synch_mode"

rcssserver $opt 1> stdout.log 2> stderr.log
# $HOME/local/bin/rcssserver $opt 1> stdout.log 2> stderr.log

sleep 1

#
# kill teams
#
if [ -x $left_path/kill ]; then
    $left_path/kill >/dev/null 2>&1
fi
if [ -x $right_path/kill ]; then
    $right_path/kill >/dev/null 2>&1
fi

#
# move csv files to log directory
#
mv ${log_name}*.csv $log_dir

#
# validate game log
#
echo "[`date "+%Y%m%d-%H%M%S"`] @$hostname validating game log..."
if command -v rcgvalidator >/dev/null 2>&1; then
    rcgvalidator ${log_dir}/${log_name}.rcg* > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "[$logtime] @$hostname rcgvalidator failed"
        exit 1
    fi
fi

#
# analyzer game log and generate compressed csv files
#
echo "[`date "+%Y%m%d-%H%M%S"`] @$hostname analyzing game log..."
if command -v rcg2csv >/dev/null 2>&1; then
    rcg2csv ${log_dir}/${log_name}.rcg* > /dev/null 2>&1
    if [ -e ${log_dir}/${log_name}.tracking.csv ]; then
        gzip -f ${log_dir}/${log_name}.tracking.csv
    fi
fi
if command -v rcg2data >/dev/null 2>&1; then
    rcg2data ${log_dir}/${log_name}.rcg* > /dev/null 2>&1
    if [ -e ${log_dir}/${log_name}.event.csv ]; then
        gzip -f ${log_dir}/${log_name}.event.csv
    fi
fi

#
# compress debug log files
#
echo "[`date "+%Y%m%d-%H%M%S"`] @$hostname compressing debug log files..."

debug_log_dir="${log_name}"
mkdir -p $debug_log_dir

# move log files
if [ -e stdout.log ]; then
	mv stdout.log ${debug_log_dir}
fi
if [ -e stderr.log ]; then
	mv stderr.log ${debug_log_dir}
fi

# move ocl files
if [ -e /tmp/HELIOS*-1.ocl ]; then
	mv /tmp/HELIOS*.ocl ${debug_log_dir}
else
	echo "[$logtime] @$hostname ocl not found"
fi

# compress and move debug log files
sleep 0.1
tar czf ${log_name}.tar.gz ${debug_log_dir}/*
rm -rf ${debug_log_dir}

mv ${log_name}.tar.gz $log_dir

if [ -x $current_path/cpufreq_set_all.sh ]; then
    $current_path/cpufreq_set_all.sh powersave
fi

echo "[`date "+%Y%m%d-%H%M%S"`] @$hostname finished."

exit 0
