def is_navbox(table):
    for ancestor in table.find_parents("div"):
        if ancestor.get("role") == "navigation" and "navbox" in (ancestor.get("class") or []):
            return True
    return False

        
def is_junk_table(
    table,
    section_title,
    lineage=None,
    first_text="",
    classes=None,
    parent_classes=None
):
    section_title = (section_title or "").lower()
    classes = classes or []
    parent_classes = parent_classes or []
    first_text = (first_text or "").lower()

    # 1. Title-based skip (strongest)
    bad_words = [
        "external links", "references", "reference", "contents",
        "see also", "bibliography", "sources", "further reading", "notes"
    ]
    if any(bad in section_title for bad in bad_words):
        return True

    # 2. Nested table skip
    for ancestor in table.find_parents():
        if ancestor.name == "table":
            return True

    # 3. Navbox skip
    if is_navbox(table):
        return True

    # 4. Parent-class skip
    junk_parent_classes = {"reflist", "references", "reference", "refbegin", "refend"}
    if any(c in parent_classes for c in junk_parent_classes):
        return True

    # 5. Table-class skip
    junk_table_classes = {"toc", "metadata"}
    if any(c in classes for c in junk_table_classes):
        return True
    if any(c.endswith("mbox") for c in classes):
        return True

    # 6. First-row skip
    junk_headings = {
        "external links", "references", "reference", "bibliography",
        "sources", "further reading", "notes", "see also",
        "contents", "contents table", "navigation menu", "related articles"
    }
    if first_text in junk_headings:
        return True

    return False
