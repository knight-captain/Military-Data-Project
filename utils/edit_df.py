from utils.nav_tree import get_name

def add_to_cell(df, idx, col, value):
    cell = df.at[idx, col]
    if isinstance(cell, list):
        cell.append(value)
    else:
        df.at[idx, col] = [value]

def normalize_cell(val):
    if isinstance(val, list):
        return "; ".join(
            v if isinstance(v, str) else get_name(v)
            for v in val
        )
    if val is not None and not isinstance(val, str):
        return get_name(val)
    return val


def collapse_lists(df):
    for col in df.columns:
        df[col] = df[col].apply(normalize_cell)
    return df


