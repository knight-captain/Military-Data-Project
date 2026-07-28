Run pipeline.py

This will

1. PHASE I: Scrape all tables from each page linked on "https://en.wikipedia.org/wiki/Lists_of_currently_active_military_equipment_by_country"
2. PHASE II: Clean the data into a usable and understandable format, accounting for the diversity of edge cases that Wikipedia provides.
3. PHASE III: Classify the data into tables of equipment & inventory. Account for tables of individual assets (usually ships) that need to be aggregated, as well as tables missing quantities. Need to be able to at the bare minimum establish the types of equipment that a country has.
4. PHASE IV: clean the values in preparation for analysis
5. PHASE V: Output a canonical table for analysis

FILE STRUCTURE (and rough order)
"Military Data Project"/
├── data/
│   ├── data_acquisition/ (PHASE I)
│   │   └── scrape_pipe.py
│   │       ├── page_list.py
│   │       ├── scrape_wiki.py
│   │       │   ├── get_soup.py
│   │       │   ├── junk_detector.py
│   │       │   └── header_detector.py
│   │       └── build_meta_table.py
│   ├── data_cleaning/ (PHASE II)
│   │   └── clean_all.py
│   │       ├── clean_columns.py
│   │       │   ├── column_name_standardizer.py
│   │       │   ├── column_remove_superfluous.py
│   │       │   └── column_split_doublewide.py
│   │       ├── clean_rows.py
│   │       │   ├── rows_detect_type.py
│   │       │   └── rows_propagate_sections.py
│   │       ├── clean_table.py
│   │       └── table_update_meta.py
│   ├── data_classification/ (PHASE III)
│   │   └── classify_equipment.py
│   │       ├── classify_tables.py
│   │       │   ├── naive_classification.py
│   │       │   └── advanced_classification.py
│   │       │       ├── compute_fingerprints.py
│   │       │       └── group_tables.py
│   │       ├── classify_columns.py
│   │       └── build_master_equipment.py
│   ├── data_refining/
│   │   └── refine_pipe.py
│   │       ├── value_cleaning.py
│   │       │   ├── fix_classes.py
│   │       │   ├── fix_quantities.py
│   │       │   └── utils.edit_df.py -> collapse_lists
│   │       └── build_final_equipment_table
│   ├── data_analysis/
│   │   └── analyze_pipe.py
│   │       └── build_country_equipment_summary.py
│   └── db/
│       ├── military_equipment_PROD.db
│       ├── military_equipment_PROD.xlsx
│       ├── runs/
│       │   └── military_equipment_TEST.db
│       └── backups/
├── ontology/
│   ├── edge_cases.csv
│   └── Military_Ontology.owl
├── utils/
│   ├── update_path.py      # Called at every phase to make a copy of the previous .db
│   ├── normalization.py
│   ├── safe_SQL_caller.py
│   ├── execute_SQL.py
│   ├── nav_tree.py         # For generating and navigating an ontological tree based on Military_Ontology.owl
│   ├── read_csv.py
│   ├── regex_match.py
│   └── edit_df.py
├── venv/
├── .env
├── pipeline.py
├── README.md
├── requirements.txt
└── run_dev.bat
