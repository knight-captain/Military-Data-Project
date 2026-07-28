import pandas as pd
from data.data_cleaning.column_name_standardizer import column_name_standardizer
from data.data_cleaning.column_remove_superfluous import remove_superfluous_columns
from data.data_cleaning.column_split_doublewide import split_doublewide


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Column-cleaning pipeline (pure in-memory).
    - split double-wide tables
    - standardize column names
    - remove superfluous columns (image, unnamed, numeric)
    Always returns a DataFrame (never None).
    """

    # 1. Detect and split double-wide tables BEFORE standardizing
    dfs = split_doublewide(df)
    if len(dfs) > 1:
        df = pd.concat(dfs, ignore_index=True)

    #TODO: there are split tables that need to be merged; i.e.: australia_table_00_submarines_collinsclass & australia_table_01_submarines_collinsclass

    # 2. Find proper column names
    df = column_name_standardizer(df)

    # Step 3: Remove superfluous columns
    # -> turns out, it did 3 things: 
    # - remove image cols (which Phase III handles), 
    # - remove numbered/unnamed cols (which column_name_standardizer handles), 
    # - and stopped cleaning tiny tables, but didn't actually drop them...
    #TODO: remove_superfluous_columns might need to be removed for being superfluous! XD
    df = remove_superfluous_columns(df)

    # 4. Guarantee a DataFrame is returned
    # (If all columns were dropped, return an empty DataFrame)
    if df is None or df.shape[1] == 0:
        return pd.DataFrame()

    return df


# do I still need this?
if __name__ == "__main__":
    # Example usage:
    # python clean_columns.py my_table_name
    import sys
    if len(sys.argv) > 1:
        clean_columns(sys.argv[1])
        print(f"Column cleaning complete for {sys.argv[1]}")
