""""Since some folks don't know proper HTML, this tries to avoid mal-formed headers"""

from bs4 import Tag

def _safe_int(value, default=1):
    """
    Convert malformed HTML attribute (e.g., '13"', '2[a]', '4†') into an int.
    Keeps only digits; falls back to default if nothing usable.
    """
    if value is None:
        return default

    cleaned = "".join(ch for ch in str(value) if ch.isdigit())
    return int(cleaned) if cleaned.isdigit() else default


def expanded_col_count(tr):
    """
    Count columns in a row, safely handling malformed colspan attributes.
    """
    total = 0
    for cell in tr.find_all(["td", "th"]):
        raw = cell.get("colspan", "1")
        total += _safe_int(raw, default=1)
    return total


def is_category_row(tr, max_cols):
    cells = tr.find_all(["td", "th"])
    if not cells:
        return False

    # Rule 1: Single cell spanning full width
    if len(cells) == 1:
        colspan = _safe_int(cells[0].get("colspan", "1"))
        if colspan >= max_cols:
            return True

    # Rule 2: All cell texts identical
    texts = [c.get_text(strip=True) for c in cells]
    if len(set(texts)) == 1:
        return True

    return False


def header_detector(table):
    """
    Given a BeautifulSoup <table>, detect the correct header row,
    reorder rows so the header is first, and return clean HTML.
    """
    rows = table.find_all("tr")
    if not rows:
        return None  # caller will skip

    # Compute max column count
    try:
        max_cols = max(expanded_col_count(tr) for tr in rows)
    except Exception:
        return None

    # Find first real header row
    header_row_index = None
    for i, tr in enumerate(rows):
        if is_category_row(tr, max_cols):
            continue
        header_row_index = i
        break

    if header_row_index is None:
        header_row_index = 0

    # Reorder rows
    ordered_rows = []

    # 1. Header row first
    ordered_rows.append(rows[header_row_index])

    # 2. Category rows BEFORE header
    for i in range(header_row_index):
        ordered_rows.append(rows[i])

    # 3. All rows AFTER header
    for i in range(header_row_index + 1, len(rows)):
        ordered_rows.append(rows[i])

    # Rebuild HTML
    html_reordered = "<table>" + "".join(str(tr) for tr in ordered_rows) + "</table>"
    return html_reordered


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
