def remove_superfluous_columns(df):
    """Removes image, thumbnail, and empty columns."""
    drop_cols = []

    for col in df.columns:
        col_lower = col.lower()

        # Image-like columns
        if any(x in col_lower for x in ["image", "photo", "thumbnail", "file"]):
            drop_cols.append(col)
            continue

        # Columns with all NaN or empty
        if df[col].isna().all():
            drop_cols.append(col)
            continue

    return df.drop(columns=drop_cols)
