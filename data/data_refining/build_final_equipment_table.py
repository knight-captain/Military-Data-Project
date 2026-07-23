import pandas as pd

def build_final_equipment_table(conn, df_master):
    """
    Build canonical_equipment table from cleaned a_master_equipment.
    Country is excluded for now.
    """

    # Columns to keep (drop country)
    keep_cols = [
        "equip_type",
        "variant",
        "other_names",

        "class_path",
        "sub_class",

        "note",

        "origin",
        "cost",
        "dates",
        "status",

        "propulsion",
        "role",
        "capability",

        "dimensions",
        "weight",
        "displacement",
        "width",
        "caliber",
        "length",
        "range",
        "speed",

        "armament",
        "carrier",
        
        "table_name",
        "url"
    ]

    # Filter to existing columns only
    keep_cols = [col for col in keep_cols if col in df_master.columns]

    df_final = df_master[keep_cols].copy()

    # Write to SQL
    df_final.to_sql(
        "a_canonical_equipment",
        conn,
        if_exists="replace",
        index=False
    )

    print("Built a_canonical_equipment table.")
