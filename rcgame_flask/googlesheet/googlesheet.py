import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from rcgame_flask.config import config

def _get_spreadsheet():
    """
    Get the entire spreadsheet.

    :return: spreadsheet
    """
    scope = ["https://spreadsheets.google.com/feeds"]

    if config.DOC_ID is None or config.KEY_PATH is None:
        print("Error: DOC_ID or KEY_PATH is not set.")
        return None

    doc_id = config.DOC_ID
    key_path = os.path.expanduser(config.KEY_PATH)

    credentials = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(doc_id)

    return spreadsheet


def _get_or_create_summary_sheet(spreadsheet):
    """
    Get the summary worksheet.
    If the summary worksheet does not exist, create a new one.

    Args:
        spread_sheet (gspread.models.Spreadsheet): The entire spreadsheet.

    :return: summary_sheet
    """

    if spreadsheet is None:
        print("Error: spread_sheet is None")
        return None

    try:
        summary_sheet = spreadsheet.worksheet("summary")
    except gspread.exceptions.WorksheetNotFound:
        print("create summary sheet")
        summary_sheet = spreadsheet.add_worksheet("summary", 100, 12)
        header = [
            "GroupName",
            "DateTime",
            "Left",
            "Right",
            "#ofGame",
            "LWin",
            "Draw",
            "RWin",
            "LGoal",
            "RGoal",
            "LWinRate",
            "DrawRate",
            "RWinRate",
            "LAveGoal",
            "RAveGoal",
            "LMaxGoal",
            "RMaxGoal",
            "L#ofScored",
            "R#ofScored",
            "LScoredRate",
            "RScoredRate",
            "Memo",
        ]
        summary_sheet.append_row(header)

    return summary_sheet


def _insert_group_summary_row(spreadsheet, group_name, group_time, left_name, right_name, memo):
    """
    Insert a new row into the summary worksheet.

    Args:
        spreadsheet (gspread.models.Worksheet): The summary worksheet.
        group_name (str): The name of the group.
        group_time (str): The date and time of the group creation.
        left_name (str): The name of the left team.
        right_name (str): The name of the right team.
        memo (str): The memo for the group.
    """
    if spreadsheet is None:
        print("Error: spread_sheet is None")
        return None

    summary_sheet = _get_or_create_summary_sheet(spreadsheet)
    if summary_sheet is None:
        print("Error: summary_sheet is None")
        return None

    # if the group_name record does not exist in the first column,
    # insert a new row at the second row of the summary sheet
    if summary_sheet.find(group_name, in_column=1) is not None:
        print("group_name already exists.")
        return

    num_match = "=G2+H2+I2"
    l_win = "=COUNTIF('" + group_name + "'!$H$1:$H$1000,1)"
    draw = "=COUNTIF('" + group_name + "'!$H$1:$H$1000,0)"
    r_win = "=COUNTIF('" + group_name + "'!$H$1:$H$1000,-1)"
    l_goal = "=SUM('" + group_name + "'!$F$1:$F$1000)"
    r_goal = "=SUM('" + group_name + "'!$G$1:$G$1000)"
    l_win_rate = "=G2/F2"
    draw_rate = "=H2/F2"
    r_win_rate = "=I2/F2"
    l_ave_goal = "=J2/F2"
    r_ave_goal = "=K2/F2"
    l_max_goal = "=MAX('" + group_name + "'!$F$1:$F$1000)"
    r_max_goal = "=MAX('" + group_name + "'!$G$1:$G$1000)"
    n_l_scored = "=COUNTIF('" + group_name + "'!$F$1:$F$1000,\">0\")"
    n_r_scored = "=COUNTIF('" + group_name + "'!$G$1:$G$1000,\">0\")"
    l_scored_rate = "=J2/F2"
    r_scored_rate = "=K2/F2"

    data = [
        group_name,
        group_time.strftime("%Y-%m-%d %H:%M:%S"),
        left_name,
        right_name,
        memo,
        num_match,
        l_win,
        draw,
        r_win,
        l_goal,
        r_goal,
        l_win_rate,
        draw_rate,
        r_win_rate,
        l_ave_goal,
        r_ave_goal,
        l_max_goal,
        r_max_goal,
        n_l_scored,
        n_r_scored,
        l_scored_rate,
        r_scored_rate,
    ]

    # insert a new row at the second row of the summary sheet
    summary_sheet.insert_row(values=data, index=2, value_input_option="USER_ENTERED")


def get_or_create_group_sheet(group_name, group_time, left_name, right_name, memo):
    """
    Get the worksheet for the group.
    If the group worksheet does not exist, create a new one.

    Args:
        group_name (str): The name of the group.
        group_time (str): The date and time of the group creation
        left_name (str): The name of the left team.
        right_name (str): The name of the right team.
        memo (str): The memo for the group.

    :return: group_sheet
    """

    spreadsheet = _get_spreadsheet()
    if spreadsheet is None:
        return None

    try:
        group_sheet = spreadsheet.worksheet(group_name)
    except gspread.exceptions.WorksheetNotFound:
        print("create a new group sheet " + group_name)
        group_sheet = spreadsheet.add_worksheet(group_name, 100, 8)

    _insert_group_summary_row(spreadsheet, group_name, group_time, left_name, right_name, memo)

    return group_sheet


def upload_group_results(group_name, group_time, left_name, right_name, memo, match_records):
    """
    Upload the match results to the Google Spreadsheet.
    """
    group_sheet = get_or_create_group_sheet(group_name, group_time, left_name, right_name, memo)
    if group_sheet is None:
        print(f"Error: Failed to get a group sheet for {group_name}")
        return False

    # Create a dictionary to store the group records
    local_records = []
    for match in match_records:
        if match.processed != "processed":
            continue

        point = (
            1
            if match.left_score > match.right_score
            else -1 if match.left_score < match.right_score
            else 0
        )
        local_records.append(
            [
                str(match.match_index).zfill(5),
                match.host_name,
                match.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                match.left_team,
                match.right_team,
                match.left_score,
                match.right_score,
                point,
            ]
        )

    group_sheet.clear()
    group_sheet.append_rows(local_records)
    return True
