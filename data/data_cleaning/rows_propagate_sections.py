import pandas as pd
import re

def propagate_sections(df, section_rows, quantity_rows, empty_rows):
    """
    Adds 'section' and/or 'quantity' columns (only if needed) and fills them downward.
    Removes section/quantity rows afterward.

    Assumes section_rows and quantity_rows were detected using:
      - all cells identical and non-empty
    """

    df = df.copy()

    # Determine whether we need these columns
    # technically don't need this, since all equipment gets all super_cols in the end
    has_section = len(section_rows) > 0
    has_quantity = len(quantity_rows) > 0
    if has_section:
        df["section"] = None
    if has_quantity:
        df["quantity"] = None

    qty_to_prop = None
    sec_to_prop = None

    for idx, row in df.iterrows():

        # Normalize row values
        values = [str(v).strip() if pd.notna(v) else "" for v in row.tolist()]
        unique_vals = set(values)

        # Extract the non-empty value
        value_to_propagate = next((v for v in unique_vals if v), "")

        # --- META ROWS ---
        if idx in section_rows or idx in quantity_rows:

            # Extract "(digits)" if present
            m = re.search(r"\(\d+\)", value_to_propagate)
            if m:
                qty_to_prop = m.group(0)   # keep parentheses, e.g. "(5)"
            else:
                qty_to_prop = None

            # Remove "(digits)" from the section text
            sec_to_prop = re.sub(r"\(\d+\)", "", value_to_propagate).strip()

            # Skip writing to df for meta rows (they get removed later)
            continue

        # --- ALL ROWS ---
        if has_quantity:
            df.at[idx, "quantity"] = qty_to_prop 

        if has_section:
            df.at[idx, "section"] = sec_to_prop


    # Remove section + quantity rows
    rows_to_drop = sorted(set(section_rows + quantity_rows + empty_rows))
    # if len(rows_to_drop) >= 5:
    #     print(f"Dropping {len(rows_to_drop)} rows!")
    df = df.drop(rows_to_drop).reset_index(drop=True)

    # Move metadata columns to the front (if they exist)
    front_cols = []
    if has_section:
        front_cols.append("section")
    if has_quantity:
        front_cols.append("quantity")

    df = df[front_cols + [c for c in df.columns if c not in front_cols]]

    return df
