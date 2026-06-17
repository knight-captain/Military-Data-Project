import sqlite3
import pandas as pd
import random
from pathlib import Path

# === CONFIG ===
DB_PATH = "data/db/military_equipment_TEST-SYNTHED.db"
OUTPUT_CSV = "data/data_exploration/column_exploration_report.csv"
SAMPLE_SIZE = 10
UNIQUE_THRESHOLD = 10

# === LOAD MASTER TABLE ===
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT * FROM a_master_equipment", conn)
conn.close()

rows = []

for col in df.columns:
    series = df[col].dropna().astype(str)

    total_vals = len(series)
    unique_vals = series.unique()
    unique_count = len(unique_vals)

    # Random sample of values
    sample_vals = random.sample(list(unique_vals), min(SAMPLE_SIZE, unique_count))

    # # If small cardinality, list all unique values
    # small_unique_list = (
    #     ", ".join(sorted(unique_vals)) if unique_count <= UNIQUE_THRESHOLD else ""
    # )

    rows.append({
        "column": col,
        "unique_count": unique_count,
        "total_non_null": total_vals,
        "ratio": f"{unique_count}/{total_vals}",
        "sample_values": "; ".join(sample_vals),
        # "all_unique_values_if_small": small_unique_list
    })

# === SAVE REPORT ===
report_df = pd.DataFrame(rows)
report_df.to_csv(OUTPUT_CSV, index=False)

print(f"Column exploration report written to: {OUTPUT_CSV}")
