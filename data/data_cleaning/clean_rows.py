import pandas as pd

from data.data_cleaning.rows_detect_type import detect_row_type
from data.data_cleaning.rows_propagate_sections import propagate_sections

def clean_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Row-cleaning pipeline (pure in-memory).
    - detect row types (section rows, quantity rows, empty rows)
    - propagate section metadata downward
    - remove empty rows
    Always returns a DataFrame (never None).
    """
    
    if df is None or df.shape[0] == 0:
        return pd.DataFrame()

    # Step 1: Detect row types
    section_rows, quantity_rows, empty_rows = detect_row_type(df)

    # Step 2: Propagate metadata downward and remove empty rows
    df = propagate_sections(df, section_rows, quantity_rows, empty_rows)

    # Step 3: Guarantee a DataFrame is returned
    if df is None:
        return pd.DataFrame()

    return df

# do I still need this?
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        clean_rows(sys.argv[1])
        print(f"Row cleaning complete for {sys.argv[1]}")
