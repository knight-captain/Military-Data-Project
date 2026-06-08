import ast
import numpy as np
import pandas as pd
from collections import Counter
from utils.normalization import normalize_text

def make_unique(colnames):
    '''Make sure every column has a name (for weird wiki colspan shenanigans)
    e.g.: <tr 1> has 5 <td>'s, but <tr 2 colspan=6>'''
    counter = Counter()
    result = []
    for col in colnames:
        counter[col] += 1
        if counter[col] == 1:
            result.append(col)
        else:
            result.append(f"{col}_{counter[col]}")
    return result

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

    # Breaks if there is a comma in one col, but not the others, just like I told Copilot
    # if isinstance(col, str) and "," in col:
    #     return len(col.split(","))

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

        # Case 3: comma-separated <- this shouln't happen, but the AI really likes it for some reason
        else:
            print("CASE 3 HIT - this DEFINITELY shouldn't happen")
            parts = [normalize_text(col)]

        temp_rows.append(parts)

    # Transpose matrix so each part of the tuple can be in a separate row
    # grouped by col [[col_1-a, col_1-b, col_1-c],[col_2-a, col_2-b, col_2-c],[col_3-a, col_3-b, col_3-c]] -> 
    # grouped by row [[col_1-a, col_2-a, col_3-a],[col_1-b, col_2-b, col_3-b],[col_1-c, col_2-c, col_3-c]]
    columns_as_rows = np.array(temp_rows, dtype=object).T.tolist()

    # Identify the row where all values differ. The first to satisfy this it the col_names
    # This is one of my favorite snippets of code! 
    col_names = None
    for row in columns_as_rows:
        if len(set(row)) == len(row):
            col_names = row
            break

    if col_names is None:
        # fallback: use first row
        col_names = columns_as_rows[0]
        print(f"used first row as default: {col_names}")

    # Build metadata row (everything except the col_names)
    new_row = []
    for parts in temp_rows:
        leftover = [x for x in parts if x not in col_names]
        new_row.append(", ".join(leftover) if leftover else None)

    # print(f"fixed column names: {col_names} & found row: {new_row}")

    return col_names, new_row


def column_name_standardizer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full column cleaning pipeline:
    - Detect multi-element headers ("type","small arms")
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

    # COMPLEX CASE: parse multi-element headers
    new_cols, new_row = parse_multi_element_column(df)
    
    # Make sure every column has a name (for weird wiki colspan shenanigans); then apply. There may be more tacked on funcs like this as we get into the weeds...
    new_cols = make_unique(new_cols)
    df.columns = new_cols

    # Insert metadata row (AFTER renaming new_cols, or it will make new cols)
    df.loc[-1] = new_row
    df.index = df.index + 1 # put it in last, then move it to the "next" idx, which is first
    df = df.sort_index()

    # CLEANUP FOR numbered cols that slipped through
    clean_cols = []
    for c in df.columns:
        c_str = str(c).strip().lower()
        if c_str.isdigit() or c_str.startswith("unnamed"):
            # if c_str.isdigit():
            #     print("WARNING: dropping numeric column in standardizer")            
            # if c_str.startswith("unnamed"):
            #     print("WARNING: dropping unnamed column in standardizer")
            continue
        clean_cols.append(c)

    #TODO: OTHER LANGUAGES. Actually, its looking like those are either ranks (and can be ignored) or object names in a non-english language, which can be kept

    df = df[clean_cols]
    df.columns = [normalize_text(str(c)) for c in df.columns]

    return df
