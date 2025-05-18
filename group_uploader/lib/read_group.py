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
