import re
from utils.normalization import normalize_text

def remove_superfluous_columns(df):
    """Removes image-like columns, unnamed/numeric columns, and empty columns."""
    drop_cols = []

    for col in df.columns:
        col_norm = normalize_text(col)
        col_norm = re.sub(r'\.\d+$', '', col_norm)

        # Remove image cols
        if any(x in col_norm for x in [
            "image", "photo", "thumbnail", "file", "picture", "illustration", "portrait", "insignia"
        ]):
            drop_cols.append(col)
            continue

        # 2. Unnamed or numeric-only columns <- might not need in column_name_standardizer.py
        col_str = str(col).strip().lower()
        if col_str.startswith("unnamed") or col_str.isdigit():
            drop_cols.append(col)
            # if col_str.isdigit():
            #     print("WARNING: dropping numeric column in superfluous")            
            # if col_str.startswith("unnamed"):
            #     print("WARNING: dropping numeric column in superfluous")
            continue

        # # 3. Columns with all NaN or empty-like values -> too aggressive
        # series = df[col]
        # if series.isna().all() or series.astype(str).str.lower().str.strip().isin(["", "nan", "none", "[null]"]).all():
        #     drop_cols.append(col)
        #     continue
    
    # if len(drop_cols) >=5:
    #     print(f"Dropping {len(drop_cols)} cols!")
    df = df.drop(columns=drop_cols)

    # 4. If the table is now empty or has only 1 column → skip it; this is a Phase III decision
    # if df.shape[1] <= 1:
    #     return None

    return df
