import re
import pandas as pd

def is_quantity_value(val: str) -> bool:
    val = val.lower().strip()
    # pure number
    if re.fullmatch(r"\d+", val):
        return True
    # ends with (number)
    if re.search(r"\(\d+\)$", val):
        return True
    # contains "active (number)" etc.
    if re.search(r"(active|in service|total)\s*\(\d+\)", val):
        return True
    return False


def detect_row_type(df: pd.DataFrame):
    """
    Detects special row types in a cleaned Wikipedia table.

    Definitions:
      - Section row:   every cell has the same non-empty value (merged header row)
      - Quantity row:  every cell has the same numeric-like value (usually a number in (x))
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
                # print(f"Found QTY col: {set(row)}")
            
            section_rows.append(idx)

            continue

        # Case 3: Normal row → ignore

    return section_rows, quantity_rows, empty_rows
