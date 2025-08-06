from pathlib import Path

def run_pipeline_on_folder(folder_path: str):
    """
    Runs the complete data extraction and processing pipeline on a local folder of PDFs.
    """
    import os
    import shutil
    from classify_and_organize_pdfs import classify_and_organize_pdfs
    from email_monitor import PharmacyEmailMonitor
    from complete_data_pipeline import run_complete_pipeline

    print(f"--- Starting Local PDF Pipeline for folder: {folder_path} ---")

    # 1. Setup temporary directories
    source_path = Path(folder_path)
    temp_classified_path = Path("temp_classified_pdfs")
    if temp_classified_path.exists():
        shutil.rmtree(temp_classified_path)
    temp_classified_path.mkdir(exist_ok=True)

    # 2. Classify and organize PDFs into the temp directory
    print("\nStep 1: Classifying and organizing PDFs...")
    classify_and_organize_pdfs(str(source_path), str(temp_classified_path))

    # 3. Deduplicate based on latest time
    print("\nStep 2: Deduplicating reports, keeping latest time...")
    monitor = PharmacyEmailMonitor()
    monitor.keep_latest_versions(str(temp_classified_path))

    # Log which reports will be imported
    if any(temp_classified_path.iterdir()):
        kept_files_log = [str(p.relative_to(temp_classified_path)) for p in sorted(temp_classified_path.rglob("*.pdf"))]
        if kept_files_log:
            print("Reports kept for importing into database:\n" + "\n".join(f"- {f}" for f in kept_files_log))
        else:
            print("No reports left to import after deduplication.")
            return
    else:
        print("No reports found to process after classification.")
        return

    # 4. Run the data extraction and combination pipeline
    print("\nStep 3: Running data extraction pipeline...")
    try:
        run_complete_pipeline(str(temp_classified_path))
        print("\n✅ Data extraction and combination complete.")
    except Exception as e:
        print(f"\n❌ Data extraction pipeline failed: {e}")
        return

    # 5. Insert data into the database
    print("\nStep 4: Inserting data into the database...")
    try:
        from insert_data_to_database import main as insert_main
        insert_main()
        print("\n✅ Data imported successfully into the database.")
    except Exception as e:
        print(f"\n❌ Database insertion failed: {e}")

    print("\n--- Local PDF Pipeline Finished ---")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        folder_to_process = sys.argv[1]
        run_pipeline_on_folder(folder_to_process)
    else:
        print("Please provide the path to the folder of PDFs as an argument.")
        print("Usage: python run_local_pipeline.py /path/to/your/pdfs") 