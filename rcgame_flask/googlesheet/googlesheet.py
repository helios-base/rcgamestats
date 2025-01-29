import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials


DOC_ID = "Your Document Id"
KEY_PATH = "Path to your json file"


def get_spreadsheet():
    """
    Get the entire spreadsheet.

    :return: spreadsheet
    """
    scope = ["https://spreadsheets.google.com/feeds"]
    doc_id = DOC_ID
    key_path = os.path.expanduser(KEY_PATH)

    credentials = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(doc_id)

    return spreadsheet


def get_or_create_summary_sheet():
    """
    Get the summary worksheet.
    If the summary worksheet does not exist, create a new one.

    :return: summary_sheet
    """

    try:
        spreadsheet = get_spreadsheet()
    except Exception as e:
        print("Error: ", e)
        return

    try:
        summary_sheet = spreadsheet.worksheet("summary")
    except gspread.exceptions.WorksheetNotFound:
        print("create summary sheet")
        summary_sheet = spreadsheet.add_worksheet("summary", 100, 12)
        header = [
            "group_name",
            "datetime",
            "left", "right",
            "memo",
            "# of game",
            "l-win", "draw", "r-win",
            "l-goal", "r-goal",
            "l win rate", "draw rate", "r win rate",
            "l ave goal", "r ave goal",
            "l max goal", "r max goal",
            "# of l scored", "# of r scored",
            "l scored rate", "r scored rate",
        ]
        summary_sheet.append_row(header)

    return summary_sheet


def insert_group_summary_row(group_name, datetime, left_name, right_name, memo):
    """
    Insert a new row into the summary worksheet.

    Args:
        group_name (str): The name of the group.
        datetime (str): The date and time of the group creation.
        left_name (str): The name of the left team.
        right_name (str): The name of the right team.
        memo (str): The memo for the group.
    """

    summary_sheet = get_or_create_summary_sheet()
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
        group_name, datetime, left_name, right_name, memo,
        num_match, l_win, draw, r_win, l_goal, r_goal,
        l_win_rate, draw_rate, r_win_rate, l_ave_goal, r_ave_goal,
        l_max_goal, r_max_goal, n_l_scored, n_r_scored, l_scored_rate, r_scored_rate
    ]

    # insert a new row at the second row of the summary sheet
    summary_sheet.insert_row(values=data, index=2, value_input_option="USER_ENTERED")


def get_group_sheet(group_name):
    """
    Get the worksheet for the group.

    Args:
        group_name (str): The name of the group.

    :return: group_sheet
    """

    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return None

    try:
        group_sheet = spreadsheet.worksheet(group_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Error: Worksheet '{group_name}' not found.")
        return None

    return group_sheet


def add_group(group_name, datetime, left_name, right_name, memo):
    """
    Create a new worksheet for the group.
    Add a new row associated with the group to the summary worksheet.

    Args:
        group_name (str): The name of the group.
        datetime (str): The date and time of the group creation.
        left_name (str): The name of the left team.
        right_name (str): The name of the right team.
        memo (str): The memo for the group.
    """

    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return None

    # Get the worksheet for the group
    # If the group worksheet does not exist, create a new one.
    try:
        group_sheet = spreadsheet.worksheet(group_name)
        print("group sheet already exists.")
    except gspread.exceptions.WorksheetNotFound:
        print("create a new group sheet " + group_name)
        group_sheet = spreadsheet.add_worksheet(group_name, 100, 8)

    # Insert a new row into the summary worksheet
    insert_group_summary_row(group_name, datetime, left_name, right_name, memo)

    return group_sheet


def upload_group_results(match_list):
    """
    Upload the group results to the Google Spreadsheet.

    """
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return

    # Create a dictionary to store the group records
    group_records = {}
    for match in match_list:
        group_name = match.group_name
        if group_name not in group_records:
            group_records[group_name] = []
        point = 1 if match.left_score > match.right_score else -1 if match.left_score < match.right_score else 0
        match_record = [
            str(match.match_index).zfill(5),
            match.host_name,
            match.start_time,
            match.left_team,
            match.right_team,
            match.left_score,
            match.right_score,
            point
        ]
        group_records[group_name].append(match_record)

    # Upload the group results
    for group_name, records in group_records.items():
        group_sheet = get_group_sheet(group_name)
        if group_sheet is None:
            print(f"Error: Failed to create a group sheet for {group_name}")
            continue

        # レコードをアップロード
        for record in records:
            group_sheet.append_row(record)
    