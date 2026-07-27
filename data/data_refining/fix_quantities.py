import re
import pandas as pd

YEAR_MIN = 1950
YEAR_MAX = 2050

SHIP_PREFIXES = ["USS", "HMS", "HS", "INS", "ČMP", "KRI", "HMAS"]

def has_multiple_ship_names(name: str) -> bool:
    #TODO: This logic is severely flawed. It makes the wrong assumptions about ambiguous ship_name
    if not isinstance(name, str):
        return False

    # obvious separators
    if "," in name or ";" in name:
        return True

    # repeated prefixes
    for prefix in SHIP_PREFIXES:
        if name.count(prefix) > 1:
            return True

    # repeated parentheses (multiple ships listed)
    if name.count("(") > 1:
        return True

    # multiple capitalized words often = multiple ships
    caps = re.findall(r"\b[A-Z][a-zA-Z]+\b", name)
    if len(caps) > 2:
        return True

    return False


def clean_quantity_value(raw: str, ship_name: str | None):
    if raw is None:
        return None

    if not isinstance(raw, str):
        return None

    raw = raw.strip()
    if not raw:
        return None

    # Ship logic: multiple ships listed → quantity = 1
    if ship_name and has_multiple_ship_names(ship_name):
        return 1

    # Extract all numbers
    nums = [int(n) for n in re.findall(r"\d+", raw)]
    if not nums:
        return None

    # Remove years unless they are the only number
    filtered = [n for n in nums if not (YEAR_MIN <= n <= YEAR_MAX)]
    if not filtered:
        filtered = nums  # keep the year if it's the only number

    # Ship logic: one ship, multiple numbers → use parentheses number
    if ship_name and len(filtered) > 1:
        m = re.search(r"\((\d+)\)", raw)
        if m:
            return int(m.group(1))
        return 1

    # Return min viable number
    return int(min(filtered))


def fix_quantities(df):
    cleaned = []

    for idx in df.index:
        raw = df.at[idx, "quantity"]
        ship_name = df.at[idx, "ship_name"]
        cleaned_val = clean_quantity_value(raw, ship_name)
        cleaned.append(cleaned_val)

    df["quantity_clean"] = cleaned
    df["quantity_clean"] = df["quantity_clean"].astype("Int64")
    return df
