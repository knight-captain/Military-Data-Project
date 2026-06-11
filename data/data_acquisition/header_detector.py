""""Since some folks don't know proper HTML, this tries to avoid mal-formed headers"""

from bs4 import Tag

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

def expanded_col_count(tr):
    total = 0
    for cell in tr.find_all(["td", "th"]):
        total += int(cell.get("colspan", "1"))
    return total

def is_category_row(tr, max_cols):
    ths = tr.find_all("th")
    if len(ths) != 1:
        return False
    colspan = int(ths[0].get("colspan", "1"))
    return colspan == max_cols

def is_header_like(tr, max_cols):
    cells = tr.find_all(["td", "th"])
    if len(cells) < 2:
        return False
    if is_category_row(tr, max_cols):
        return False
    if expanded_col_count(tr) != max_cols:
        return False

    # Heuristic: header rows rarely contain pure numbers
    texts = [c.get_text(strip=True) for c in cells]
    numeric_like = sum(t.isdigit() for t in texts)
    if numeric_like >= len(texts) / 2:
        return False

    return True
