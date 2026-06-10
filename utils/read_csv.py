import csv
import numpy as np
import re
from pathlib import Path

# RAW LIST READER (each row is a single string)
def to_list(path):
    """
    Return CSV as a list of raw string rows.
    No parsing, no splitting.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


# LIST-OF-LISTS READER (safe CSV parsing)
def to_list_of_lists(path):
    """
    Return CSV as a list of lists using Python's CSV parser.
    Handles commas inside quotes, escaped quotes, etc.
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return [row for row in reader]


# list of dicts (header = key → other cells in row = value)
def to_list_of_dicts(path):
    """
    Load CSV into a list of dictionaries using the header row.
    Validates row lengths and warns on mismatches.
    """
    path = Path(path)

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return []

    header = rows[0]
    num_cols = len(header)

    clean_rows = []

    for row in rows[1:]:
        if len(row) == num_cols:
            clean_rows.append(row)
        elif len(row) > num_cols:
            print(f"[CSV WARNING] Row has too many columns: {row}")
        elif len(row) < num_cols:
            print(f"[CSV WARNING] Row is missing columns: {row}")
        else:
            print(f"[CSV WARNING] Unexpected row format: {row}")

    # Convert clean rows to list-of-dicts
    dicts = []
    for row in clean_rows:
        dicts.append(dict(zip(header, row)))

    return dicts

# DICT KEYED BY FIRST COLUMN, value is the second column
def to_dict(path):
    """
    Load CSV into a dict keyed by the first column.
    Values are the second column.
    WILL NOT save the header row.
    """
    rows = to_list_of_lists(path)
    data_rows = rows[1:]
    out = {}
    for row in data_rows:
        if not row:
            continue
        out[row[0]] = row[1]
    return out

# DICT KEYED BY FIRST COLUMN
def to_dict_of_lists(path):
    """
    Load CSV into a dict keyed by the first column.
    Values are lists of the remaining columns.
    """
    rows = to_list_of_lists(path)
    data_rows = rows[1:]
    out = {}
    for row in data_rows:
        if not row:
            continue
        key = row[0]
        out[key] = row[1:]
    return out

# NUMPY ARRAY (column-count validation)
def to_array(path):
    """
    Load CSV into a numpy array.
    Validates that all rows have the same number of columns.
    Skips header row.
    """
    rows = to_list_of_lists(path)
    header = rows[0]
    num_cols = len(header)

    array_rows = []

    for row in rows[1:]:
        if len(row) == num_cols:
            array_rows.append(row)
        elif len(row) > num_cols:
            print(f"[CSV WARNING] {row} has more columns than {rows[0]}")
        elif len(row) < num_cols:
            print(f"[CSV WARNING] {row} has fewer columns than {rows[0]}")
        else:
            print(f"[CSV WARNING] Unexpected row format: {row}")

    return np.array(array_rows)

# SET OF FIRST-COLUMN VALUES
def to_set(path):
    rows = to_list_of_lists(path)
    return {row[0] for row in rows[1:] if row}
