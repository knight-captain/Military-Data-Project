import pandas as pd

    # keep_cols = [
    #     "equip_type",
    #     "variant",
    #     "other_names",
        
    #     #TODO: remove these when quantity stabilizes 
    #     "quantity", 
    #     "quantity_clean",

    #     "class_path",
    #     "sub_class",

    #     "note",

    #     "origin",
    #     "cost",
    #     "dates",
    #     "status",

    #     "propulsion",
    #     "role",
    #     "capability",

    #     "dimensions",
    #     "weight",
    #     "displacement",
    #     "width",
    #     "caliber",
    #     "length",
    #     "range",
    #     "speed",

    #     "armament",
    #     "carrier",
        
    #     "table_name",
    #     "url"
    # ]


def build_final_equipment_table(conn, df_master):
    """
    Build a_canonical_equipment table from the full cleaned a_master_equipment.
    Keep ALL columns for now. We'll pare down later when aggregation stabilizes.
    """

    df_final = df_master.copy()

    df_final.to_sql(
        "a_canonical_equipment",
        conn,
        if_exists="replace",
        index=False
    )

    print("Built a_canonical_equipment table with all columns.")
