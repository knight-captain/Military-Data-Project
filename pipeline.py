'''
Each phase follows the following:

if RUN_PHASE:
    this_phase_path = run_phase(previous_phase_path)
else:
    this_phase_path = path to military_equipment_TEST-PHASE.DB
'''
from pathlib import Path

# --- Modules ---
from data.data_acquisition.scrape_pipe import scrape_pipe
from data.data_cleaning.clean_all import clean_all
from data.data_synthesis.synthesize_equipment import synthesize_equipment


RUN_SCRAPER = False #If False, make sure a set of military_equipment_TEST.db exists; can also be str, and will run edge_case.txt and name the .db after the str
RUN_CLEANING = True
RUN_SYNTHESIZER = True

def run_pipeline():
    # Phase I: Scrape or load existing RAW
    if RUN_SCRAPER is not False:
        print("\n=== PHASE I: SCRAPING TABLES ===")
        raw_path = scrape_pipe(RUN_SCRAPER)
    else:
        proxy_scrape = Path("data/db/military_equipment_TEST.db") # Make sure this exists & == a raw scrape
        raw_path = Path(str(proxy_scrape).replace("TEST.db", "TEST-RAW.db"))
        if not raw_path.exists():
            raise FileNotFoundError(
                f"Skipping cleaning, but CLEANED DB not found: {raw_path}"
            )

    # Phase II: Clean or load existing CLEANED
    if RUN_CLEANING:
        print("\n=== PHASE II: CLEANING TABLES ===")
        cleaned_path = clean_all(db_path=raw_path)
    else:
        # Load previously cleaned DB
        cleaned_path = Path(str(raw_path).replace("-RAW.db", "-CLEANED.db"))
        if not cleaned_path.exists():
            raise FileNotFoundError(
                f"Skipping cleaning, but CLEANED DB not found: {cleaned_path}"
            )

    # Phase III: Synthesis or load existing SYNTHED
    if RUN_SYNTHESIZER:
        print("\n=== PHASE III: SYNTHESIZING DATA ===")
        synthed_path = synthesize_equipment(db_path=cleaned_path)
    else:
        # Load previously synthesized DB
        synthed_path = Path(str(cleaned_path).replace("-CLEANED.db", "-SYNTHED.db"))
        if not synthed_path.exists():
            raise FileNotFoundError(
                f"Skipping synthesis, but SYNTHED DB not found: {synthed_path}"
            )

    print("\n=== PIPELINE COMPLETE ===")

if __name__ == "__main__":
    run_pipeline()
