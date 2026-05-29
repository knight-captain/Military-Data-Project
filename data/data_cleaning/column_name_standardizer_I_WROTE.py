import numpy as np
import pandas as pd
from data.utils.normalization import normalize_text

def detect_column_elements(col):
    if isinstance(col, tuple):
        return len(list(col))
    elif isinstance(col, str) and "," in col:
        return len(col.split(","))
    else:
        return 1
    
def parse_multi_element_column(df,num_elements):
    # This function would contain the logic to parse columns with multiple elements
    # For example, it could split the column into multiple rows based on the number of elements
    col_names = []
    temp_rows = []

    for col in df.columns:
        parts = []
        if isinstance(col, tuple):
            parts = list(col)
        elif isinstance(col, str) and "," in col:
            parts = col.split(",")
        else:
            # I Don't even know... if we got here by accident, just return the original column and a blank row
            parts = [col]
            return parts, None # this might break the new_row, but we shouldn't see this
        temp_rows.append(parts)
    
    #flip the [[x,y,...], [a,b,...],...] to [[x,a,...], [y,b,...],...]
    columns_as_rows = np.array(temp_rows).T.tolist()

    for row in columns_as_rows:
        # if every value is different in the row, then we can use it as the column name
        if len(set(row)) == len(row):
            col_names = row
            break
    
    #remove the col_names from temp_rows then combine all the other elements into a single row
    new_row = []
    for col in temp_rows:
        row_elements = [x for x in col if x not in col_names]
        new_row.extend(row_elements)

    return col_names, new_row

    
def column_name_standardizer(df: pd.DataFrame) -> pd.DataFrame:
    new_cols = []

    for col in df.columns:
        num_elements = detect_column_elements(col)
        if num_elements == 1:
            new_cols.append(normalize_text(str(col)))
        elif num_elements > 1:
            # Handle columns with multiple elements
            new_cols, new_rows = parse_multi_element_column(df, num_elements)

    # if there is new row data, add it to the dataframe (this would be the section/quantity metadata)
    if new_rows:
        df = pd.concat([df, pd.DataFrame([new_rows], columns=new_cols)], ignore_index=True)

    df.columns = new_cols

    return df