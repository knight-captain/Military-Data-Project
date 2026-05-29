import pandas as pd

def propagate_sections(df, section_rows, count_rows):
    """
    Adds 'section' and 'count' columns and fills them downward.
    Removes both section and count rows afterward.
    """

    df = df.copy()
    df["section"] = None
    df["count"] = None

    section_to_propagate = None
    count_to_propagate = None

    for idx, row in df.iterrows():

        # --- SECTION ROWS ---
        if idx in section_rows:
            val = str(row.iloc[0]).strip()
            section_to_propagate = val
            # do NOT write to df here — this row will be removed
            continue

        # --- COUNT ROWS ---
        if idx in count_rows:
            val = str(row.iloc[0]).strip()
            count_to_propagate = val
            # do NOT write to df here — this row will be removed
            continue

        # --- NORMAL ROWS ---
        df.at[idx, "section"] = section_to_propagate
        df.at[idx, "count"] = count_to_propagate

    # Remove both section and count rows
    rows_to_drop = sorted(set(section_rows + count_rows))
    df = df.drop(rows_to_drop)

    # Move section + count columns to the front
    cols = ["section", "count"] + [c for c in df.columns if c not in ("section", "count")]
    df = df[cols]

    return df
