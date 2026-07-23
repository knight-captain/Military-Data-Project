from data.data_refining.fix_classes import fix_classes
from utils.edit_df import collapse_lists
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
    cleaned_master_equipment = collapse_lists(standardized_names_master)
    print(cleaned_master_equipment.applymap(type).head())
    for col in cleaned_master_equipment.columns:
        for idx, val in cleaned_master_equipment[col].items():
            if not isinstance(val, (str, int, float, type(None))):
                print("BAD VALUE:", col, idx, val, type(val))
                raise SystemExit


    return cleaned_master_equipment