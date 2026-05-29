import sqlite3
from data.data_cleaning.clean_columns import clean_columns
from data.data_cleaning.clean_rows import clean_rows


def clean_all(db_path="data/db/military_equipment.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = cursor.execute("SELECT table_name FROM a_meta_table").fetchall()
    tables = [t[0] for t in tables]

    conn.close()
    ###
    # TODO: what are the ethical and efficient ramifications of oppening and closing the DB connection for each table? 
    # Should we just do it once here and pass the connection to the cleaning functions?
    # and then just make each clean_ func able to open it if necessary?
    ###
    for table in tables:
        if table.startswith("a_"):
            continue

        print(f"Cleaning {table}...")
        clean_columns(table, db_path=db_path)
        #clean_rows(table, db_path=db_path) #<- not ready to clean rows yet, fix columns first

    print("All tables cleaned.")

if __name__ == "__main__":    clean_all()