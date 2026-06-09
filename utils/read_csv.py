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


# DICT-OF-DICTS (header → value)
def to_dicts(path):
    """
    Load CSV into a list of dictionaries using the header row.
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# DICT KEYED BY FIRST COLUMN
def to_dict(path):
    """
    Load CSV into a dict keyed by the first column.
    Values are lists of the remaining columns.
    """
    rows = to_list_of_lists(path)
    header = rows[0]
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
            print(f"[CSV WARNING] Row has too many columns: {row}")
        elif len(row) < num_cols:
            print(f"[CSV WARNING] Row is missing columns: {row}")
        else:
            print(f"[CSV WARNING] Unexpected row format: {row}")

    return np.array(array_rows)

# SET OF FIRST-COLUMN VALUES
def to_set(path):
    rows = to_list_of_lists(path)
    return {row[0] for row in rows[1:] if row}

def to_regex_rules(path, category_col="CATEGORY", type_col="TYPE", regex_col="REGEX"):
    """
    Load a CSV of regex rules into a list of rule objects:
        {
            "category": <string>,
            "type": <string>,
            "pattern": <compiled regex>
        }

    This is used by categorize_tables.py.
    """
    rows = to_dicts(path)
    rules = []

    for row in rows:
        rules.append({
            "category": row[category_col].strip(),
            "type": row[type_col].strip().lower(),
            "pattern": re.compile(row[regex_col], re.IGNORECASE)
        })

    return rules