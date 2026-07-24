import re
from utils.nav_tree import get_name

ESTIMATE_WORDS = {
    "several", "many", "numerous", "thousands", "hundreds",
    "unknown", "unk", "approx", "approx.", "c.", "circa"
}

def classify_quantity_token(token: str, ship_name: str | None):
    token = token.strip()
    if not token:
        return None

    if token.startswith("ε"):
        num = re.sub(r"[^\d]", "", token)
        return int(num) if num else 1

    m = re.search(r"\((\d+)\)", token)
    if m:
        class_count = int(m.group(1))
        if ship_name:
            return 1
        return class_count

    if re.fullmatch(r"\d+", token):
        num = int(token)
        if num > 50000:
            return None
        return num

    m = re.search(r"(\d+)\s*[-–]\s*(\d+)", token)
    if m:
        low, high = int(m.group(1)), int(m.group(2))
        return high

    low_val = token.lower()
    if any(word in low_val for word in ESTIMATE_WORDS):
        return None

    if re.fullmatch(r"\d{4}", token):
        return None

    nums = re.findall(r"\d+", token)
    if nums:
        return max(int(n) for n in nums)

    return None

def clean_quantity_value(raw: str, ship_name: str | None):
    if raw is None:
        return None

    val = str(raw).strip()
    if not val:
        return None

    parts = [p for p in val.split(";") if p.strip()]
    cleaned_parts = [
        classify_quantity_token(part, ship_name)
        for part in parts
    ]
    cleaned_parts = [c for c in cleaned_parts if c is not None]

    if not cleaned_parts:
        return None

    return max(cleaned_parts)

def fix_quantities(df):
    cleaned = []

    for idx in df.index:
        raw = df.at[idx, "quantity"]
        ship_name = df.at[idx, "ship_name"]
        cleaned_val = clean_quantity_value(raw, ship_name)
        cleaned.append(cleaned_val)

    df["quantity_clean"] = cleaned
    return df
