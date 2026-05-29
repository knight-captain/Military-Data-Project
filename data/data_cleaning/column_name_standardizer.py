import ast
import numpy as np
import pandas as pd
from data.utils.normalization import normalize_text


def detect_column_elements(col):
    """Return number of elements in a multi-element header."""
    if isinstance(col, tuple):
        return len(col)

    if isinstance(col, str) and col.startswith("(") and col.endswith(")"):
        try:
            parsed = ast.literal_eval(col)
            if isinstance(parsed, tuple):
                return len(parsed)
        except Exception:
            pass

    if isinstance(col, str) and "," in col:
        return len(col.split(","))

    return 1


def parse_multi_element_column(df):
    """
    Extracts multi-element header structure:
    - Builds a matrix of header parts
    - Transposes it
    - Finds the row where all values differ (real column names)
    - Everything else becomes metadata
    """

    temp_rows = []

    for col in df.columns:

        # Case 1: true tuple
        if isinstance(col, tuple):
            parts = [normalize_text(x) for x in col]

        # Case 2: stringified tuple
        elif isinstance(col, str) and col.startswith("(") and col.endswith(")"):
            try:
                parsed = ast.literal_eval(col)
                if isinstance(parsed, tuple):
                    parts = [normalize_text(x) for x in parsed]
                else:
                    parts = [normalize_text(col)]
            except Exception:
                parts = [normalize_text(col)]

        # Case 3: comma-separated <- this shouln't happen
        elif isinstance(col, str) and "," in col:
            print("CASE 3 HIT - this shouldn't happen")
            parts = [normalize_text(x) for x in col.split(",")]

        # Case 4: simple column <- this shouldn't happen
        else:
            print("CASE 4 HIT - this DEFINITELY shouldn't happen")
            parts = [normalize_text(col)]

        temp_rows.append(parts)

    # Transpose matrix
    columns_as_rows = np.array(temp_rows, dtype=object).T.tolist()

    # Identify the row where all values differ. The first to satisfy this it the col_names
    col_names = None
    for row in columns_as_rows:
        if len(set(row)) == len(row):
            col_names = row
            break

    if col_names is None:
        # fallback: use first row
        col_names = columns_as_rows[0]

    # Build metadata row (everything except the header row)
    new_row = []
    for parts in temp_rows:
        leftover = [x for x in parts if x not in col_names]
        new_row.append(", ".join(leftover) if leftover else None)

    print(f"fixed column names: {col_names} & found row: {new_row}")

    return col_names, new_row


def column_name_standardizer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full column cleaning pipeline:
    - Detect multi-element headers
    - Parse them
    - Insert metadata row only when needed
    - Normalize all column names
    """

    # Detect if any column has multiple elements
    multi = any(detect_column_elements(col) > 1 for col in df.columns)

    if not multi:
        # Simple case: just normalize column names
        df.columns = [normalize_text(str(c)) for c in df.columns]
        return df

    # Complex case: parse multi-element headers
    new_cols, new_row = parse_multi_element_column(df)

    # Insert metadata row
    df = pd.concat([df, pd.DataFrame([new_row], columns=new_cols)], ignore_index=True)

    # Apply new column names
    df.columns = new_cols

    return df
