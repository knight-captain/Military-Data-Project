import sqlite3
import pandas as pd

conn = sqlite3.connect("data/db/military_equipment_260601182948.db")

# Load the meta-column table
df = pd.read_sql_query("SELECT * FROM a_meta_table_of_columns", conn)

# Count non-null entries per column
counts = df.notna().sum().sort_values(ascending=False)

print(counts)
counts.to_csv("column_frequency.csv")