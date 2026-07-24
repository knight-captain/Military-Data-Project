from data.data_synthesis.naive_classification import classify_naively
from data.data_synthesis.advanced_classification import classify_advanced
from utils.execute_SQL import get_a_meta_table, get_a_meta_table_of_columns
from utils.nav_tree import *
import re

def classify_tables(conn):
    # 1. Load metadata
    a_meta_table = get_a_meta_table(conn)
    a_meta_table_of_columns = get_a_meta_table_of_columns(conn)

    # 2. Build unified metadata object
    SQL_table_info = {}
    for table_name, meta in a_meta_table.items():
        SQL_table_info[table_name] = {
            "section_h2": meta["section_h2"],
            "section_h3": meta["section_h3"],
            "section_h4": meta["section_h4"],
            "url": meta["url"],
            "country": meta.get("country"),
            "raw_cols": a_meta_table_of_columns.get(table_name, {}).get("raw_cols", [])
        }

    # 3. Naive classification (no more get_relationships)
    table_classes = {}
    equipment_assigned = 0

    for table_name, meta in a_meta_table.items():

        headers = (
            meta["section_h2"],
            meta["section_h3"],
            meta["section_h4"]
        )

        # classify_naively uses nav_tree internally
        result = classify_naively(headers)

        # Attach metadata needed for fingerprints
        result["raw_cols"] = SQL_table_info[table_name]["raw_cols"]
        result["country"] = SQL_table_info[table_name]["country"]
        result["url"] = SQL_table_info[table_name]["url"]

        # Compute leaf header
        headers_ordered = [
            SQL_table_info[table_name]["section_h4"],
            SQL_table_info[table_name]["section_h3"],
            SQL_table_info[table_name]["section_h2"]
        ]
        for header in headers_ordered:
            if header:
                result["leaf_header"] = header
                break

        # Compute class_path using nav_tree
        eq_class = result["equipment_class"]
        if eq_class:
            # 0 = Equipment, 1 = Aircraft/Vessel/Vehicle/System/SmallArm
            result["class_path"] = get_ancestral_path(eq_class)
        else:
            result["class_path"] = None

        table_classes[table_name] = result

        if result["equipment_class"] is not None:
            equipment_assigned += 1

    print(f"Naive: {equipment_assigned}/{len(a_meta_table)} tables classified")

    # 4. Advanced classification (uses nav_tree internally)
    table_classes = classify_advanced(table_classes)

    # 5. Count final equipment assignments
    final_equipment_assigned = sum(
        1 for t in table_classes.values()
        if t["equipment_class"] is not None
    )

    print(f"Advanced: {final_equipment_assigned}/{len(a_meta_table)} tables classified")
    # print(table_classes)

    return table_classes
'''
table_classes = {
    table_name: TableClassInfo,
    ...
}
'''
'''
TableClassInfo = {
    "equipment_class": str,        # exactly one class
    "other_classes": list[str],    # zero or many
    "confidence": float | None     # optional
}
'''