def add_to_cell(df, idx, col, value):
    cell = df.at[idx, col]
    if isinstance(cell, list):
        cell.append(value)
    else:
        df.at[idx, col] = [value]

def collapse_lists(df):
    for col in df.columns:
        for idx in df.index:
            val = df.at[idx, col]
            if isinstance(val, list):
                df.at[idx, col] = "; ".join(str(v) for v in val)
    return df