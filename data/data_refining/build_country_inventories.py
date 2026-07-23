def build_country_inventories(conn, df_master):
    """
    Build a_country_inventory table from cleaned a_master_equipment.
    """

    # Columns to include
    inv_cols = [
        "country",
        "quantity",
        "class_path",
        "sub_class",
        "equip_type",
        "variant",
        "other_names",
        "notes"
    ]

    # Only keep columns that actually exist
    inv_cols = [col for col in inv_cols if col in df_master.columns]

    # Filter down to just the inventory columns
    df_inventory = df_master[inv_cols].copy()

    # Write to SQL
    df_inventory.to_sql(
        "a_country_inventory",
        conn,
        if_exists="replace",
        index=False
    )

    print("Built a_country_inventory table.")
