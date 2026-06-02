def split_doublewide(df):
    cols = list(df.columns)
    n = len(cols)

    # Must be even number of columns
    if n % 2 != 0:
        return [df]

    half = n // 2
    left_cols = cols[:half]
    right_cols = cols[half:]

    # Normalize for comparison
    # I finally found a use for a lambda function!
    norm = lambda c: str(c).strip().lower()

    if all(norm(a) == norm(b) for a, b in zip(left_cols, right_cols)):
        # Split into two DataFrames
        left = df.iloc[:, :half].copy()
        right = df.iloc[:, half:].copy()

        # Drop empty rows
        left = left.dropna(how="all")
        right = right.dropna(how="all")
        
        print("found a double-table")
        return [left, right]

    return [df]


