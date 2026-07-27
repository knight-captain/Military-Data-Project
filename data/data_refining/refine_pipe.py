import shutil
import sqlite3
from utils.update_path import update_path

#submodules:
from data.data_refining.value_cleaning import clean_all_values
from data.data_refining.build_final_equipment_table import build_final_equipment_table
from data.data_refining.build_country_inventories import build_country_inventories

def refine_pipe(db_path=None):

    if db_path is None:
        raise ValueError("db_path must be provided.")

    # Build REFINED path & Copy SYNTHED → REFINED, then connect to the new .db
    refined_path = update_path(db_path)
    shutil.copy(db_path, refined_path)
    conn = sqlite3.connect(refined_path)

    #TODO: this should be combined with previous phase in the pipe
    print("\n[1/3] Cleaning a_master_equipment values...")
    cleaned_master_equipment = clean_all_values(conn)

    print("\n[2/3] Building a complete table of equipment ...")
    build_final_equipment_table(conn, cleaned_master_equipment)

    # print("\n[3/3] Building country inventory tables...")
    # build_country_inventories(conn, cleaned_master_equipment)
    
    conn.close()
    print("\nEquipment refining pipeline completed successfully.")

    return refined_path
