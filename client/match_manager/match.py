import os
import csv
import logging
from datetime import datetime
from config import config
from team_manager import get_team_path
from .match_runner import MatchRunner

logger = logging.getLogger("client")


class Match:
    """
    The Match object represents a match between two teams.
    """

    def __init__(self, match_id, host_id, group_name, index, left_team_name, right_team_name, log_file_name):
        """
        Initialize the Match object.
        """
        self.match_id = match_id
        self.host_id = host_id
        self.match_token = None
        self.group_name = group_name
        self.index = index
        self.left_team_name = left_team_name
        self.right_team_name = right_team_name
        self.left_team_version = None
        self.right_team_version = None
        self.left_score = -1
        self.right_score = -1
        self.log_file_name = log_file_name
        self.synch_mode = True


    def __str__(self):
        return f"{self.group_name}/{self.index}, {self.left_team_name} vs {self.right_team_name}, {self.left_score}-{self.right_score}"

    @staticmethod
    def from_json(json_data):
        """
        Create a Match object from the JSON data.
        """
        try:
            match_id = json_data["match_id"]
            host_id = json_data.get("host_id")
            match_token = json_data["match_token"]
            group_name = json_data["group_name"]
            index = json_data["index"]
            left_team_name = json_data["left_team_name"]
            right_team_name = json_data["right_team_name"]
            left_team_version = json_data["left_team_version"]
            right_team_version = json_data["right_team_version"]
            left_score = json_data.get("left_score", -1)
            right_score = json_data.get("right_score", -1)
            log_file_name = json_data["log_file_name"]
            synch_mode = json_data.get("synch_mode", True)
        except KeyError:
            return None

        match = Match(match_id, host_id, group_name, index, left_team_name, right_team_name, log_file_name)
        match.match_token = match_token
        match.left_team_version = left_team_version
        match.right_team_version = right_team_version
        match.left_score = left_score
        match.right_score = right_score
        match.synch_mode = synch_mode
        return match

    def to_json(self):
        """
        Convert the Match object to a JSON object.
        """
        return {
            "match_id": self.match_id,
            "match_token": self.match_token,
            "group_name": self.group_name,
            "left_team_name": self.left_team_name,
            "right_team_name": self.right_team_name,
            "left_team_version": self.left_team_version,
            "right_team_version": self.right_team_version,
            "left_score": self.left_score,
            "right_score": self.right_score,
            "log_file_name": self.log_file_name,
            "synch_mode": self.synch_mode,
        }

    def set_result(self, result_csv):
        """
        Set the score information from the result file.
        """
        if not os.path.exists(result_csv):
            logger.error(f"The result csv file does not exist.")
            return

        left_score = -1
        right_score = -1
        with open(result_csv, "r") as f:
            reader = csv.DictReader(f, skipinitialspace=True)
            for row in reader:
                try:
                    if row["left score"]:
                        left_score = int(row["left score"])
                    if row["right score"]:
                        right_score = int(row["right score"])
                except ValueError:
                    continue

                if left_score != -1 and right_score != -1:
                    break

        self.left_score = left_score
        self.right_score = right_score

    def run(self):
        """
        Run the match.
        """
        # def preexec_function():
        #     signal.signal(signal.SIGINT, signal.SIG_IGN)

        # log_dir = os.path.join(config.LOG_DIR, self.group_name)
        log_dir = config.TEMPORAL_DIR
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # args = [self.left_team_name, self.right_team_name, log_dir, self.log_file_name]
        # print(f"[{datetime.now().strftime('%Y%m%d-%H%M%S')}] (Match::run) args:", args)
        # process = subprocess.Popen([config.RUN_SCRIPT] + args, preexec_fn=preexec_function)
        # process.wait()

        # command = f"{config.RUN_SCRIPT} {self.left_team_name} {self.right_team_name} {log_dir} {self.log_file_name}"
        left_path = get_team_path(self.left_team_name, self.left_team_version)
        right_path = get_team_path(self.right_team_name, self.right_team_version)
        # synch_mode_str = "1" if self.synch_mode else "0"

        # command = f"{config.RUN_SCRIPT} {left_path} {right_path} {synch_mode_str} {log_dir} {self.log_file_name}"
        # exit_code = os.system(command)

        # if exit_code != 0:
        #     logger.error(f"Error running the match.")
        #     return False

        runner = MatchRunner(left_path, right_path, self.synch_mode, log_dir, self.log_file_name)
        if not runner.run():
            return False

        result_csv = os.path.join(log_dir, f"{self.log_file_name}.result.csv")
        self.set_result(result_csv)
        return True
