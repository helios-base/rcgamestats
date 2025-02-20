import os
import glob


def exist_rcl_and_rcg_file(directory, base_filename):
    rcg = os.path.join(directory, base_filename + ".rcg*")
    rcg_candidates = glob.glob(rcg)
    rcl = os.path.join(directory, base_filename + ".rcl*")
    rcl_candidates = glob.glob(rcl)
    return len(rcg_candidates) > 0 and len(rcl_candidates) > 0


def get_log_filenames(directory):
    result_files = os.path.join(directory, "*.result.csv")
    filenames = []
    for result_file in glob.glob(result_files):
        base = result_file[:-len(".result.csv")]
        if exist_rcl_and_rcg_file(directory, base):
            filenames.append(base)
    return filenames
