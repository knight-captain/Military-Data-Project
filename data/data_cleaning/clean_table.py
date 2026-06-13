import pandas as pd

def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Table-level cleaning (pure in-memory).
    Only drop tables that are truly empty or structurally meaningless.
    """

    # Drop if df is None or empty
    if df is None or df.shape[0] == 0:
        return pd.DataFrame()

    # Drop if no columns
    if df.shape[1] == 0:
        return pd.DataFrame()

    # Drop if ALL columns are junk (unnamed, numeric, auto-generated)
    cols = [str(c).lower().strip() for c in df.columns]
    if all(c.isdigit() or c.startswith("unnamed") or c.startswith("col_") for c in cols):
        print("unnamed/numbered in clean_table")
        return pd.DataFrame()

    # DO NOT drop:
    # - single-data-row tables
    # - single-column tables = list
    # - sparse tables
    # - tables with only 1–2 meaningful columns
    # - tables with only 1 data row
    # - tables with repeated headers (Phase II handles them)

    return df


if __name__ == "__main__":
    # Example usage:
    # python clean_columns.py my_table_name
    import sys
    if len(sys.argv) > 1:
        clean_table(sys.argv[1])
        print(f"Table cleanup complete for {sys.argv[1]}")