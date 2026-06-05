Run pipeline.py

This will

1. PHASE I: Scrape all tables from each page linked on "https://en.wikipedia.org/wiki/Lists\_of\_currently\_active\_military\_equipment\_by\_country"
2. PHASE II: Clean the data into a usable and understandable format, accounting for the diversity of edge cases that Wikipedia provides.
3. PHASE III: Synthesize the data into tables of equipment \& inventory. Account for tables of individual assets (usually ships) that need to be aggregated) as well as tables missing quantities. Need to be able to at the bare minimum establish the types of equipment that a country has.
4. PHASE IV: Re-scrape \& clean the equipment stats from that page if it has it. Other data might be pulled from the original tables. Important data includes cost for each piece of equipment: ship size \& armament, aircraft generation, range and armament, etc.
5. PHASE V: Visualizations \& conclusions

FILE STRUCTURE
"Military Data Project"/
├── data/
│   ├── data_acquisition/
│   │   ├── build_meta_table.py
│   │   ├── scrape_wiki.py
│   │   ├── __init__.py
│   │   └── TODO scrape_equipment.py
│   ├── data_cleaning/
│   │   ├── clean_columns.py
│   │   ├── clean_rows.py
│   │   ├── clean_table.py
│   │   ├── column_name_standardizer.py
│   │   ├── column_remove_superfluous.py
│   │   ├── column_split_doublewide.py
│   │   ├── rows_detect_type.py
│   │   ├── rows_propagate_sections.py
│   │   ├── table_update_meta.py
│   │   ├── __init__.py
│   │   └── (future cleaning scripts for equipment data)
│   ├── data_exploration/
│   │   ├── (exploration scripts)
│   │   ├── (missing‑data discovery scripts)
│   │   ├── __init__.py
│   │   ├── build_rank_dump.py
│   │   └── rank_tables.txt
│   ├── data_synthesis/
│   │   ├── build_master_equipment.py
│   │   ├── __init__.py
│   │   └── (future synthesis scripts)
│   └── db/
│       ├── military_equipment.db
│       ├── military_equipment_TEST.db
│       ├── military_equipment_TESTED.db
│       └── backups/
├── ontology/
│   ├── column_mapping.csv
│   ├── super_columns.txt
│   └── (future ontology files)
├── utils/
│   ├── get_country_for_table.py
│   ├── normalization.py
│   └── __init__.py
├── venv/
├── .env
├── pipeline.py
├── README.md
├── requirements.txt
└── run_dev.bat
