import pandas as pd

from detect_row_type import detect_row_type
from propagate_sections import propagate_sections
from remove_superfluous_columns import remove_superfluous_columns
from update_meta_columns import update_meta_columns

def clean_table(conn, table_name):
    df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)

    # Skip meta tables
    if table_name.startswith("a_meta_"):
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        return df

    # 0. Fix coloumn names <-Edited/Broke after using, so fix before rerunning.
    #column_name_standardizer
    
    # 1. Detect section rows
    section_rows, count_rows, empty_rows = detect_row_type(df)


    # 2. Propagate section labels downward
    df = propagate_sections(df, section_rows, count_rows)

    # 2.5 Delete empty_rows
    #
    
    # # 3. Remove junk columns
    # df = remove_superfluous_columns(df)

    # 4. Update meta-columns table
    update_meta_columns(conn, table_name, df)

    # 5. Save cleaned table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    return df
