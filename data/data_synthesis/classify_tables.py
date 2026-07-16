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
            "raw_cols": a_meta_table_of_columns.get(table_name, [])
        }

    # 3. Load ontology relationships
    parents, children, paths, rules = get_relationships("ontology/Military_Ontology.owl")

    # 4. Naive classification
    table_classes = {}
    equipment_assigned = 0

    for table_name, meta in a_meta_table.items():
        headers = (
            meta["section_h2"],
            meta["section_h3"],
            meta["section_h4"]
        )

        result = classify_naively(headers, rules, paths)

        # Attach metadata needed for fingerprints
        result["raw_cols"] = SQL_table_info[table_name]["raw_cols"]
        result["leaf_header"] = SQL_table_info[table_name]["section_h4"]

        table_classes[table_name] = result

        if result["equipment_class"] is not None:
            equipment_assigned += 1

    print(f"Naive: {equipment_assigned}/{len(a_meta_table)} tables classified")

    # 5. Advanced classification (run ONCE)
    table_classes = classify_advanced(table_classes, paths)

    # 6. Count final equipment assignments
    final_equipment_assigned = sum(
        1 for t in table_classes.values()
        if t["equipment_class"] is not None
    )

    print(f"Advanced: {final_equipment_assigned}/{len(a_meta_table)} tables classified")

    return table_classes #dict[table_name] = single_class_from_ontology

'''
TableClassInfo = {
    "equipment_class": str,        # exactly one class
    "other_classes": list[str],    # zero or many
    "confidence": float | None     # optional
}
'''
'''
table_classes = {
    table_name: TableClassInfo,
    ...
}
'''