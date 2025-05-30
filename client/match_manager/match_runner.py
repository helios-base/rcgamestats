import os
import glob
import time
import subprocess
import shutil
import socket
import tarfile
import logging
from config import config

logger = logging.getLogger("client")


class MatchRunner:
    """
    The MatchRunner object is responsible
    for running the matches.
    """

    def __init__(self, left_team_path, right_team_path, synch_mode, log_dir, log_name):
        """
        Initialize the MatchRunner object.
        """
        self.logtime = time.strftime("%Y%m%d-%H%M%S")
        self.hostname = config.HOST_NAME if config.HOST_NAME else socket.gethostname()
        self.left_path = left_team_path
        self.right_path = right_team_path
        self.synch_mode = synch_mode
        self.log_dir = log_dir
        self.log_name = log_name
        self.left_name = os.path.basename(self.left_path)
        self.right_name = os.path.basename(self.right_path)
        self.team_l_start = os.path.join(self.left_path, "start.sh")
        self.team_r_start = os.path.join(self.right_path, "start.sh")

    def build_options(self):
        """
        Build the options for rcssserver.
        """
        options = [
            "server::game_logging=true",
            "server::text_logging=true",
            "server::game_log_dated=true",
            "server::text_log_dated=false",
            "server::game_log_fixed=true",
            "server::text_log_fixed=true",
            "server::game_log_fixed_name=", f"'{self.log_name}'",
            "server::text_log_fixed_name=", f"'{self.log_name}'",
            "server::game_log_compression=9",
            "server::text_log_compression=9",
            "server::game_log_dir=", f"'{self.log_dir}'",
            "server::text_log_dir=", f"'{self.log_dir}'",
            "server::nr_normal_halfs=2",
            "server::nr_extra_halfs=0",
            "server::penalty_shoot_outs=false",
            "server::half_time=300",
            "server::extra_half_time=100",
            "server::synch_mode=", f"{str(self.synch_mode).lower()}",
            "server::auto_mode=true",
            "server::connect_wait=100",
            "server::team_l_start=", f"'{self.team_l_start}'",
            "server::team_r_start=", f"'{self.team_r_start}'",
            "CSVSaver::save=true",
            "CSVSaver::filename=", f"'{self.log_name}.result.csv'"
        ]
        return options

    def validate_environment(self):
        """
        Check the start.sh files and log directory.
        """
        if not os.access(self.team_l_start, os.X_OK):
            logger.error(f"Team {self.left_name} start.sh is not executable.")
            return False
        if not os.access(self.team_r_start, os.X_OK):
            logger.error(f"Team {self.right_name} start.sh is not executable.")
            return False
        if not os.path.isdir(self.log_dir):
            logger.error(f"Log directory {self.log_dir} does not exist.")
            return False
        return True

    def remove_old_files(self):
        """
        Remove old files in the working directory and the log directory.
        """
        user_working_dir = os.getcwd()
        for f in glob.glob(os.path.join(user_working_dir, "*.csv")):
            if os.path.isfile(f):
                os.remove(f)
                logger.info(f"Removed old file: {f}")
        for f in glob.glob(os.path.join(user_working_dir, "*.log")):
            if os.path.basename(f) == "client.log":
                continue
            if os.path.isfile(f):
                os.remove(f)
                logger.info(f"Removed old file: {f}")
        for f in glob.glob(os.path.join(self.log_dir, f"{self.log_name}*")):
            if os.path.isfile(f):
                os.remove(f)
                logger.info(f"Removed old file: {f}")
            if os.path.isdir(f):
                shutil.rmtree(f)
                logger.info(f"Removed old directory: {f}")

    def run_rcssserver(self, opt):
        """
        Run the rcssserver.
        """
        # logger.info(f"Running command: rcssserver {opt}")
        logger.info(f"start rcssserver: {self.log_name}")
        with open("stdout.log", "w") as stdout_file, open("stderr.log", "w") as stderr_file:
            result = subprocess.run(["rcssserver"] + opt, stdout=stdout_file, stderr=stderr_file)
        if result.returncode != 0:
            logger.error("rcssserver failed.")
            return False
        return True

    def kill_team_processes(self):
        """
        Kill the team processes.
        """
        for kill_script in [os.path.join(self.left_path, "kill"), os.path.join(self.right_path, "kill")]:
            if os.access(kill_script, os.X_OK):
                subprocess.run([kill_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"Executed kill: {kill_script}")

    def validate_game_log(self):
        logger.info("Validating game log...")
        if shutil.which("rcgvalidator"):
            log_file_pattern = os.path.join(self.log_dir, f"{self.log_name}.rcg*")
            matching_files = glob.glob(log_file_pattern)
            if not matching_files:
                logger.error(f"rcg file not found: {log_file_pattern}")
                return False
            selected = max(matching_files, key=os.path.getctime)
            # logger.info(f"Selected rcg file: {selected}")
            cmd = ["rcgvalidator", selected]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                logger.info("rcgvalidator passed.")
            except subprocess.CalledProcessError:
                logger.error("rcgvalidator failed.")
                return False
        else:
            logger.warning("rcgvalidator not found.")
        return True

    def analyze_game_log(self):
        # logger.info("Analyzing game log...")
        log_file_pattern = os.path.join(self.log_dir, f"{self.log_name}.rcg*")
        matching_files = glob.glob(log_file_pattern)
        if not matching_files:
            logger.error(f"rcg file not found: {log_file_pattern}")
            return
        selected = max(matching_files, key=os.path.getctime)
        # logger.info(f"Selected rcg file: {selected}")

        if config.USE_RCG2CSV:
            if shutil.which("rcg2csv"):
                try:
                    subprocess.run(["rcg2csv", selected], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    # result = subprocess.run(["rcg2csv", selected])
                    tracking_csv = os.path.join(self.log_dir, f"{self.log_name}.tracking.csv")
                    if os.path.exists(tracking_csv):
                        subprocess.run(["gzip", "-f", tracking_csv])
                    logger.info(f"rcg2csv completed. {self.log_name}")
                except subprocess.CalledProcessError:
                    logger.error("rcg2csv failed.")
            else:
                logger.warning("rcg2csv not found.")

        if config.USE_RCG2DATA:
            if shutil.which("rcg2data"):
                try:
                    subprocess.run(["rcg2data", selected], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    # result = subprocess.run(["rcg2data", selected])
                    event_csv = os.path.join(self.log_dir, f"{self.log_name}.event.csv")
                    if os.path.exists(event_csv):
                        subprocess.run(["gzip", "-f", event_csv])
                    logger.info(f"rcg2data completed. {self.log_name}")
                except subprocess.CalledProcessError:
                    logger.error("rcg2data failed.")
            else:
                logger.warning("rcg2data not found.")

    def run_loganalyzer3(self, side="l"):
        """
        Run loganalyzer3 for the specified side ('l' or 'r').
        """
        # look for compressed game log
        pattern = os.path.join(self.log_dir, f"{self.log_name}.rcl.gz")
        files = glob.glob(pattern)
        if not files:
            logger.error(f"No game log found for loganalyzer3: {pattern}")
            return False

        selected = max(files, key=os.path.getctime)
        if not shutil.which("loganalyzer3"):
            logger.warning("loganalyzer3 not found.")
            return False
        try:
            logger.info(f"Running loganalyzer3: loganalyzer3 {selected} --side {side} --output-dir {self.log_dir}")
            # ensure output_dir ends with a slash
            output_dir = self.log_dir if self.log_dir.endswith(os.path.sep) else self.log_dir + os.path.sep

            subprocess.run(
                ["loganalyzer3", selected, "--side", side, "--output-dir", output_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            logger.info("loganalyzer3 completed successfully.")

            # === CSV ファイルを <self.log_name>.csv にリネーム ===
            for csv_path in glob.glob(os.path.join(self.log_dir, "*.csv")):
                dst = os.path.join(self.log_dir, f"{self.log_name}.csv")
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(csv_path, dst)

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"loganalyzer3 failed (exit={e.returncode})")
            return False    
    
    def move_csv_files(self):
        """
        Move the csv files to the log directory.
        """
        user_working_dir = os.getcwd()
        # logger.info(f"Moving CSV files from {user_working_dir} to {self.log_dir}")
        for f in glob.glob(os.path.join(user_working_dir, f"{self.log_name}*.csv*")):
            filename = os.path.basename(f)
            # logger.info(f"Found CSV file: {filename}")
            if os.path.isfile(f):
                dst = os.path.join(self.log_dir, filename)
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(f, dst)

    def compress_debug_logs(self):
        user_working_dir = os.getcwd()

        debug_log_dir = self.log_name
        os.makedirs(debug_log_dir, exist_ok=True)

        # move stdout and stderr logs
        for log_file in ["stdout.log", "stderr.log"]:
            log_path = os.path.join(user_working_dir, log_file)
            if os.path.exists(log_path):
                dst = os.path.join(debug_log_dir, f"{log_file}")
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(log_path, dst)
        logger.info(f"Moved console logs to {debug_log_dir}")

        # move ocl files
        ocl_files = glob.glob("/tmp/HELIOS*.ocl")
        if ocl_files:
            for f in ocl_files:
                dst = os.path.join(debug_log_dir, os.path.basename(f))
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(f, dst)
            logger.info(f"Moved ocl to {debug_log_dir}")
        else:
            logger.info("ocl not found.")

        # compress the debug log directory
        archive_name = f"{debug_log_dir}.tar.gz"
        with tarfile.open(archive_name, "w:gz") as tar:
            tar.add(debug_log_dir, arcname=os.path.basename(debug_log_dir))
        shutil.rmtree(debug_log_dir)
        logger.info(f"Compressed to {archive_name}")

        # move the archive to the log directory
        dst = os.path.join(self.log_dir, archive_name)
        if os.path.exists(dst):
            os.remove(dst)
        try:
            shutil.move(archive_name, dst)
            logger.info(f"Moved {archive_name}")
        except Exception as e:
            logger.error(f"Failed to move {archive_name}: {e}")

    def check_cpufreq_info_available(self):
        """
        Check if the cpufreq-info command is available.
        """
        if not shutil.which("cpufreq-info"):
            logger.warning("cpufreq-info not found.")
            return False

        try:
            subprocess.run(
                ["sudo", "-n", "cpufreq-set", "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except subprocess.CalledProcessError:
            logger.warning("cpufreq-set cannot be executed without password.")
            return False

        return True

    def change_cpufreq(self, governor):
        """
        Change the CPU frequency governor.
        """
        if not config.CHANGE_CPUFREQ:
            return

        if not self.check_cpufreq_info_available():
            return

        num_cpus = os.cpu_count()
        if not num_cpus:
            logger.warning("Number of CPUs cannot be determined.")
            return

        for cpu in range(num_cpus):
            try:
                result = subprocess.run(
                    ["sudo", "-n", "cpufreq-set", "-c", str(cpu), "-g", governor],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                if result.returncode != 0:
                    logger.error("cpufreq-set execution failed.")
                    return
            except subprocess.CalledProcessError:
                logger.error("cpufreq-set failed.")
                return

    def run(self):
        """
        Run the match.
        """
        logger.info(f"Run match: {self.left_name} vs {self.right_name} / {self.log_name.split('-')[0]}")

        if not self.validate_environment():
            return False
        self.remove_old_files()

        options = self.build_options()
        self.change_cpufreq("performance")
        if not self.run_rcssserver(options):
            return False

        self.kill_team_processes()
        if not self.validate_game_log():
            return False
        self.analyze_game_log()
        self.run_loganalyzer3(side="l")
        self.move_csv_files()
        self.compress_debug_logs()
        self.change_cpufreq("powersave")

        logger.info("Completed the match.")

        return True


# Test the MatchRunner class
# Usage:
# PYTHONPATH=..:$PYTHONPATH python match_runner.py

if __name__ == "__main__":
    try:
        from run import init_logging
        init_logging()
    except ImportError:
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s [%(levelname)s] %(message)s",
                            handlers=[logging.StreamHandler()])

    left_team_path = os.path.expanduser("~/rcgamestats/teams/helios2024/v1/helios2024")
    right_team_path = os.path.expanduser("~/rcgamestats/teams/cyrus2024/v1/cyrus2024")
    synch_mode = True
    log_dir = os.path.expanduser("~/rcgamestats/log")
    log_name = "rcssserver"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    match_runner = MatchRunner(left_team_path, right_team_path, synch_mode, log_dir, log_name)
    match_runner.run()
