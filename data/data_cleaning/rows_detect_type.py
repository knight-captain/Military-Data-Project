import re
import pandas as pd

# Patterns that count as "numeric" for quantity rows
COUNT_PATTERNS = [
    r"active\s*\(\d+\)",
    r"in service\s*\(\d+\)",
    r"total\s*\d+",
    r"\(\d+\)",             # parentheses with numbers
    r"^\d+$",               # pure numbers
    r"^\d{4}$",             # years
    r"^\d+\s*$"             # numeric-only with whitespace
]

def is_quantity_value(val: str) -> bool:
    """Return True if the value matches any quantity/count pattern."""
    for pat in COUNT_PATTERNS:
        if re.fullmatch(pat, val.lower()):
            return True
    return False


def detect_row_type(df: pd.DataFrame):
    """
    Detects special row types in a cleaned Wikipedia table.

    Definitions:
      - Section row:   every cell has the same non-empty value (merged header row)
      - Quantity row:  every cell has the same numeric-like value (per COUNT_PATTERNS)
      - Empty row:     every cell is empty or NaN

    Returns:
        section_rows:  list of row indexes
        quantity_rows: list of row indexes
        empty_rows:    list of row indexes
    """

    section_rows = []
    quantity_rows = []
    empty_rows = []

    for idx, row in df.iterrows():
        # Normalize values
        values = [str(v).strip() if pd.notna(v) else "" for v in row.tolist()]
        unique_vals = set(values)

        # Case 1: Entire row empty
        if unique_vals == {""}:
            empty_rows.append(idx)
            continue

        # Case 2: All values identical AND non-empty
        # This triggers for single-column tables, which is ok.
        if len(unique_vals) == 1:
            val = next(iter(unique_vals))

            # Quantity row?
            if is_quantity_value(val):
                quantity_rows.append(idx)
            else:
                section_rows.append(idx)

            continue

        # Case 3: Normal row → ignore

    return section_rows, quantity_rows, empty_rows
