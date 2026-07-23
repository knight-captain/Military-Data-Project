from data.data_refining.fix_classes import fix_classes
from utils.execute_SQL import get_table

def clean_all_values(conn):
    a_master_equipment = get_table(conn,"a_master_equipment")

    print("Fixing sub_classes...")
    # Fix sub_class & class_path
    fixed_classes_master = fix_classes(a_master_equipment)

    print("Fixing quantities...")
    # Clean quantity
    cleaned_quantity_master = fixed_classes_master
    
    print("Standardizeing equipment names...")
    # Standardize equip_name
    standardized_names_master = cleaned_quantity_master

    #anything else?
    cleaned_master_equipment = standardized_names_master
    return cleaned_master_equipment