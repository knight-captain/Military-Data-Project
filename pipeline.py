'''
Each phase follows the following:

if RUN_PHASE:
    this_phase_path = run_phase(previous_phase_path)
else:
    this_phase_path = path to military_equipment_TEST-PHASE.DB
'''
from datetime import datetime
from pathlib import Path

# --- Modules ---
from data.data_acquisition.scrape_pipe import scrape_pipe
from data.data_cleaning.clean_all import clean_all
from data.data_synthesis.synthesize_equipment import synthesize_equipment
from data.data_refining.refine_pipe import refine_pipe
from data.data_analysis.analyze_pipe import analyze_data


RUN_SCRAPER = False #If False, make sure a set of military_equipment_TEST.db exists; can also be str, and will run edge_case.txt and name the .db after the str
RUN_CLEANING = False
RUN_SYNTHESIZER = False
RUN_REFINER = False
RUN_ANALYZER = True

def run_pipeline():
    stamp = datetime.now().strftime("%H%M%S")
    print(f"Started Pipe: {stamp}")

    # Phase I: Scrape
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

    # Phase II: Clean
    if RUN_CLEANING:
        print("\n=== PHASE II: CLEANING TABLES ===")
        stamp = datetime.now().strftime("%H%M%S")
        print(f"Started Cleaning: {stamp}")
        cleaned_path = clean_all(db_path=raw_path)
    else:
        # Load previously cleaned DB
        cleaned_path = Path(str(raw_path).replace("-RAW.db", "-CLEANED.db"))
        if not cleaned_path.exists():
            raise FileNotFoundError(
                f"Skipping cleaning, but CLEANED DB not found: {cleaned_path}"
            )

    # Phase III: Synthesis
    if RUN_SYNTHESIZER:
        print("\n=== PHASE III: SYNTHESIZING DATA ===")
        stamp = datetime.now().strftime("%H%M%S")
        print(f"Started Synth: {stamp}")
        synthed_path = synthesize_equipment(db_path=cleaned_path)
    else:
        # Load previously synthesized DB
        synthed_path = Path(str(cleaned_path).replace("-CLEANED.db", "-SYNTHED.db"))
        if not synthed_path.exists():
            raise FileNotFoundError(
                f"Skipping synthesis, but SYNTHED DB not found: {synthed_path}"
            )

    # Phase IV: Refine
    if RUN_REFINER:
        print("\n=== PHASE IV: REFINING DATA ===")
        stamp = datetime.now().strftime("%H%M%S")
        print(f"Started Refine: {stamp}")
        refined_path = refine_pipe(db_path=synthed_path)
    else:
        # Load previously synthesized DB
        refined_path = Path(str(synthed_path).replace("-SYNTHED.db", "-REFINED.db"))
        if not synthed_path.exists():
            raise FileNotFoundError(
                f"Skipping synthesis, but REFINED DB not found: {refined_path}"
            )

    # Phase V: Analysis
    if RUN_ANALYZER:
        print("\n=== PHASE V: ANALYZING DATA ===")
        stamp = datetime.now().strftime("%H%M%S")
        print(f"Started Analysis: {stamp}")
        analyzed_path = analyze_data(db_path=refined_path)
    else:
        # Load previously synthesized DB
        analyzed_path = Path(str(refined_path).replace("-REFINED.db", "-ANALYZED.db"))
        if not analyzed_path.exists():
            raise FileNotFoundError(
                f"Skipping synthesis, but ANALYZED DB not found: {analyzed_path}"
            )

    stamp = datetime.now().strftime("%H%M%S")
    print(f"Finished Pipe: {stamp}")
    print("\n=== PIPELINE COMPLETE ===")


if __name__ == "__main__":
    run_pipeline()
