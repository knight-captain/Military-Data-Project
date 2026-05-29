import re
import pandas as pd

# Patterns that indicate a COUNT row, not a category
COUNT_PATTERNS = [
    r"active\s*\(\d+\)",
    r"in service\s*\(\d+\)",
    r"total\s*\d+",
    r"\(\d+\)",             # parentheses with numbers
    r"^\d+$",               # pure numbers
    r"^\d{4}$",             # years
    r"^\d+\s*$"             # numeric-only
]

def is_count_value(value):
    """Returns True if the value indicates a count row."""
    if not isinstance(value, str):
        return False
    value = value.lower().strip()
    return any(re.search(p, value) for p in COUNT_PATTERNS)


def row_values(df, row):
    """Extract values from meaningful columns only."""
    cols = [
        c for c in df.columns
        if not c.startswith("_")
        and c not in ("scrape_url", "scrape_timestamp", "source_url")
    ]
    return [str(row[c]).strip() if pd.notna(row[c]) else "" for c in cols]


def is_repeat_row(values):
    non_empty = [v for v in values if v != ""]

    # If there's only one non-empty value, it's NOT a repeat row
    if len(non_empty) <= 1:
        return False

    # Case 1: all values identical
    if len(set(values)) == 1 and values[0] != "":
        return True

    # Case 2: first value present, others blank (but only if >1 columns exist)
    if values[0] != "" and all(v == "" for v in values[1:]):
        return True

    # Case 3: first value repeated across all columns
    if values[0] != "" and all(v == values[0] for v in values):
        return True

    return False


def detect_row_type(df):
    """
    Returns:
        section_rows: list of row indices that are category rows
        count_rows: list of row indices that are count rows
    """

    section_rows = []
    count_rows = []
    empty_rows = []

    for idx, row in df.iterrows():
        vals = row_values(df, row)

        # returns rows with no meaningful values
        if all(v == "" for v in vals):
            empty_rows.append(idx)
            continue

        # Check if it's a repeat row
        if is_repeat_row(vals):
            # Now classify it
            first_val = vals[0]

            if is_count_value(first_val):
                count_rows.append(idx)
            else:
                section_rows.append(idx)
            continue
        
        #don't do anything with other types of rows

    return section_rows, count_rows, empty_rows
