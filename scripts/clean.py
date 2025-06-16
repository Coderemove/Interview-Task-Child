import sys
import os
import pandas as pd

# Add scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Now import path_utils - ADD get_dataset_path to the import
from path_utils import safe_read_csv, get_output_path, get_dataset_path, DATASET_KEYS, DIRECTORY_KEYS

def load_excel_sheets(file_path):
    """Reads an Excel file and returns a dictionary of DataFrames keyed by sheet name."""
    xl = pd.ExcelFile(file_path)
    sheets_dict = {sheet: xl.parse(sheet) for sheet in xl.sheet_names}
    return sheets_dict

def check_sheet_duplicates(sheet_name, df):
    """Print duplicate details for the sheet using the 'RowHash' column."""
    if 'RowHash' not in df.columns:
        print(f"No 'RowHash' column found in sheet: {sheet_name}")
        return
    
    duplicates = df[df.duplicated(subset=['RowHash'], keep=False)]
    if duplicates.empty:
        print(f"No duplicates found in sheet: {sheet_name}")
    else:
        print(f"Duplicates found in sheet: {sheet_name}")
        for rowhash, group in duplicates.groupby('RowHash'):
            if group.drop_duplicates().shape[0] == 1:
                print(f"Identical duplicates found for RowHash: {rowhash}")
            else:
                print(f"Non-identical duplicates found for RowHash: {rowhash}")
                print(group)
    print("\n")

def remove_sheet_duplicates(sheet_name, df):
    """Remove duplicates from the sheet based on the 'RowHash' column."""
    if 'RowHash' not in df.columns:
        print(f"No 'RowHash' column found in sheet: {sheet_name}. Skipping duplicate removal.")
        return df
    
    original_count = len(df)
    df_cleaned = df.drop_duplicates(subset=['RowHash'])
    removed_count = original_count - len(df_cleaned)
    
    if removed_count > 0:
        print(f"Removed {removed_count} duplicate(s) from sheet: {sheet_name}")
    else:
        print(f"No duplicates removed from sheet: {sheet_name}")
    
    return df_cleaned

# Main execution
try:
    # Use centralized path management
    excel_file_path = get_dataset_path(DATASET_KEYS['INSTAGRAM_ANALYTICS_EXCEL'])
    excel_sheets = load_excel_sheets(excel_file_path)
    
    # Remove unwanted sheets
    excel_sheets.pop('SupermetricsQueries', None)

    # Check for duplicates
    for sheet_name, df in excel_sheets.items():
        check_sheet_duplicates(sheet_name, df)

    # Remove duplicates
    for sheet_name, df in excel_sheets.items():
        excel_sheets[sheet_name] = remove_sheet_duplicates(sheet_name, df)

    # Clean specific sheets
    if "Instagram Top Cities Regions" in excel_sheets:
        df = excel_sheets["Instagram Top Cities Regions"]
        if "City" in df.columns:
            df = df.drop(columns=["City"])
            excel_sheets["Instagram Top Cities Regions"] = df
            print("Removed 'City' column from 'Instagram Top Cities Regions' sheet.\n")

    # Remove RowHash columns
    for sheet_name, df in excel_sheets.items():
        if "RowHash" in df.columns:
            df = df.drop(columns=["RowHash"])
            excel_sheets[sheet_name] = df
            print(f"Removed 'RowHash' column from sheet: {sheet_name}\n")

    # Clean Instagram Post Engagement
    if "Instagram Post Engagement" in excel_sheets:
        df = excel_sheets["Instagram Post Engagement"]
        if "Media ID" in df.columns:
            df = df.drop(columns=["Media ID"])
            excel_sheets["Instagram Post Engagement"] = df
            print("Dropped 'Media ID' column from 'Instagram Post Engagement' sheet.\n")

    # Export cleaned data using safe paths
    for sheet_name, df in excel_sheets.items():
        safe_filename = f"{sheet_name}.csv"
        output_path = get_output_path(DIRECTORY_KEYS['DATASET'], safe_filename)
        df.to_csv(output_path, index=False)
        print(f"Exported sheet '{sheet_name}' to {output_path}\n")
        
    print("✓ Data cleaning completed successfully")
        
except Exception as e:
    print(f"Error in clean.py: {e}")
    import traceback
    traceback.print_exc()






