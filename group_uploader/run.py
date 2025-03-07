import argparse
from lib.config import config
from lib.read_group import get_results
from lib.create_group import create_group
from lib.submit_results import submit_results

# Example usage:
# python run.py --server-url http://127.0.0.1:5000 \
#  --api-key xxxxx \
#  --group-dir ./log/20250220-183344-helios2024-cyrus2024 \
#  --group-name 20250220-183344-helios2024-cyrus2024 \
#  --left-team-name helios2024 --left-team-version v1 \
#  --right-team-name cyrus2024 --right-team-version v1

# python run.py -u http://127.0.0.1:5000 
# -a xxxxx
# -g ~/rcgamestats/log/20250220-173721-helios2024-cyrus2024 
# -n 20250220-173721-helios2024-cyrus2024 
# -l helios2024 -L v1 -r cyrus2024 -R v1

parser = argparse.ArgumentParser(description="Group uploader")
parser.add_argument("-u", "--server-url", required=True, help="The URL of the server", default="http://127.0.0.1:5000")
parser.add_argument("-H", "--host-name", required=False, help="The name of the host", default="localhost")
parser.add_argument("-a", "--api-key", required=True, help="The API key")
parser.add_argument("-g", "--group-dir", required=True, help="The directory containing the group files")
parser.add_argument("-n", "--group-name", required=True, help="The name of the group")
parser.add_argument("-l", "--left-team-name", required=True, help="The name of the team on the left")
parser.add_argument("-L", "--left-team-version", required=False, help="The version of the team on the left")
parser.add_argument("-r", "--right-team-name", required=True, help="The name of the team on the right")
parser.add_argument("-R", "--right-team-version", required=False, help="The version of the team on the right")
parser.add_argument("-d", "--description", help="The description of the group")
args = parser.parse_args()


#
# update config using arguments
#
config.update_from_args(args)

#
# read result files
#
results = get_results(config.GROUP_DIR)
if not results or len(results) == 0:
    print(f"No group files found in {config.GROUP_DIR}")
    exit(1)

#
# create group
#
group_data = create_group(results)
if group_data is None:
    print("Failed to create group")
    exit(1)

#
# submit results
#
submit_results(group_data, results)
