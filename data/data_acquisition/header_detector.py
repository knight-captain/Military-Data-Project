""""Since some folks don't know proper HTML, this tries to avoid mal-formed headers"""

from bs4 import Tag

def _safe_int(value, default=1):
    """
    Convert a malformed HTML attribute (e.g., '13"', '2[a]', '4†') into an int.
    Keeps only digits; falls back to default if nothing usable.
    """
    if value is None:
        return default

    # Strip non-digit characters
    cleaned = "".join(ch for ch in str(value) if ch.isdigit())

    if cleaned.isdigit():
        return int(cleaned)

    return default


def expanded_col_count(tr):
    """
    Count columns in a row, safely handling malformed colspan attributes.
    """
    total = 0
    for cell in tr.find_all(["td", "th"]):
        raw = cell.get("colspan", "1")
        total += _safe_int(raw, default=1)
    return total

#TODO: this will take some fine-tuning:
def is_category_row(tr, max_cols):
    cells = tr.find_all(["td", "th"])
    if not cells:
        return False

    # Extract text values
    texts = [c.get_text(strip=True) for c in cells]

    # Rule 1: Single cell spanning full width
    if len(cells) == 1:
        raw = cells[0].get("colspan", "1")
        colspan = _safe_int(raw, default=1)
        if colspan >= max_cols:
            return True

    # Rule 2: Expanded row where all values are identical
    if len(set(texts)) == 1:
        return True

    return False

'''The Graveyard of Failed Header-selectors'''
# def is_merged_row(tr):
#     if not isinstance(tr, Tag):
#         return False
#     cells = [c for c in tr.find_all(["td", "th"]) if isinstance(c, Tag)]
#     return any(int(c.get("colspan", "1")) > 1 for c in cells)

# def is_repeated_row(tr):
#     if not isinstance(tr, Tag):
#         return False
#     cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"]) if isinstance(c, Tag)]
#     return len(cells) > 0 and len(set(cells)) <= 1

# def is_header_like(tr):
#     if not isinstance(tr, Tag):
#         return False
#     cells = [c for c in tr.find_all(["td", "th"]) if isinstance(c, Tag)]
#     if len(cells) < 2:
#         return False
#     if is_merged_row(tr):
#         return False
#     if is_repeated_row(tr):
#         return False
#     return True

# def is_header_like(tr, max_cols):
#     cells = tr.find_all(["td", "th"])
#     if len(cells) < 2:
#         return False
#     if is_category_row(tr, max_cols):
#         return False
#     if expanded_col_count(tr) != max_cols:
#         return False

#     # Heuristic: header rows rarely contain pure numbers
#     texts = [c.get_text(strip=True) for c in cells]
#     numeric_like = sum(t.isdigit() for t in texts)
#     if numeric_like >= len(texts) / 2:
#         return False

#     return True
