import os
import csv
import glob


def exist_rcl_and_rcg_file(directory, base_filename):
    rcg = os.path.join(directory, base_filename + ".rcg*")
    rcg_candidates = glob.glob(rcg)
    rcl = os.path.join(directory, base_filename + ".rcl*")
    rcl_candidates = glob.glob(rcl)
    return len(rcg_candidates) > 0 and len(rcl_candidates) > 0


def get_scores(result_file):
    left_score = -1
    right_score = -1
    with open(result_file, "r") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for row in reader:
            try:
                if row["left score"]:
                    left_score = int(row["left score"])
                if row["right score"]:
                    right_score = int(row["right score"])
            except ValueError:
                return None, None
            except KeyError:
                return None, None
        return left_score, right_score

    return None, None

def get_domination_time(loganalyzer3_file):
    our_domination_time = 0
    opp_domination_time = 0
    with open(loganalyzer3_file, "r") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for row in reader:
            try:
                if row["our dominate time"]:
                    our_domination_time = int(row["our_domination_time"])
                if row["opp dominate time"]:
                    opp_domination_time = int(row["opp_domination_time"])
            except ValueError:
                return None, None
            except KeyError:
                return None, None
        return our_domination_time, opp_domination_time

def get_results(directory):
    result_files = os.path.join(directory, "*.result.csv")
    results = []
    for result_file in glob.glob(result_files):
        left_score, right_score = get_scores(result_file)
        if left_score is None or right_score is None:
            continue
        base = os.path.basename(result_file)[:-len(".result.csv")]
        if exist_rcl_and_rcg_file(directory, base):
            results.append((base, left_score, right_score))
    return results

def get_loganalyzer3(directory):
    loganalyzer3_files = os.path.join(directory, "*.loganalyzer3.csv")
    loganalyzer3 = []
    for loganalyzer3_file in glob.glob(loganalyzer3_files):
        our_domination_time, opp_domination_time = get_domination_time(loganalyzer3_file)
        if our_domination_time is None or opp_domination_time is None:
            continue
        base = os.path.basename(loganalyzer3_file)[:-len(".loganalyzer3.csv")]
        if exist_rcl_and_rcg_file(directory, base):
            loganalyzer3.append((base, our_domination_time, opp_domination_time))
    return loganalyzer3