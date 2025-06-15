import pandas as pd
import os

def load_excel_sheets(file_path):
    """
    Reads an Excel file and returns a dictionary of DataFrames keyed by sheet name.
    """
    xl = pd.ExcelFile(file_path)
    sheets_dict = {sheet: xl.parse(sheet) for sheet in xl.sheet_names}
    return sheets_dict

def check_sheet_duplicates(sheet_name, df):
    """
    Print duplicate details for the sheet using the 'RowHash' column.
    """
    print(f"Sheet: {sheet_name}")
    if 'RowHash' not in df.columns:
        print("Column 'RowHash' not found in this sheet.\n")
        return

    duplicate_count = df.duplicated(subset='RowHash', keep='first').sum()
    print(f"Total duplicate entries in 'RowHash': {duplicate_count}")
    
    duplicates = df[df.duplicated(subset='RowHash', keep=False)]
    if duplicates.empty:
        print("No duplicate rows found.\n")
        return

    grouped = duplicates.groupby('RowHash')
    for rowhash, group in grouped:
        if len(group) > 1:
            first_row = group.iloc[0].drop('RowHash')
            identical = True
            for _, row in group.iloc[1:].iterrows():
                if not row.drop('RowHash').equals(first_row):
                    identical = False
                    break
            if identical:
                print(f"Identical duplicates found for RowHash: {rowhash}")
            else:
                print(f"Non-identical duplicates found for RowHash: {rowhash}")
                print(group)
    print("\n")

def remove_sheet_duplicates(sheet_name, df):
    """
    Remove duplicate rows from df using the 'RowHash' column (keeps first occurrence)
    and print how many rows were removed.
    """
    print(f"Cleaning sheet: {sheet_name}")
    if 'RowHash' not in df.columns:
        print("Column 'RowHash' not found. Skipping cleaning.\n")
        return df

    initial_count = len(df)
    df_cleaned = df.drop_duplicates(subset='RowHash', keep='first')
    removed_count = initial_count - len(df_cleaned)
    print(f"Removed {removed_count} duplicate row(s) based on 'RowHash'.\n")
    return df_cleaned

excel_file = 'dataset/Copy of Instagram_Analytics - DO NOT DELETE (for interview purposes).xlsx'
excel_sheets = load_excel_sheets(excel_file)
excel_sheets.pop('SupermetricsQueries', None)

for sheet_name, df in excel_sheets.items():
    check_sheet_duplicates(sheet_name, df)

for sheet_name, df in excel_sheets.items():
    excel_sheets[sheet_name] = remove_sheet_duplicates(sheet_name, df)

if "Instagram Top Cities Regions" in excel_sheets:
    df = excel_sheets["Instagram Top Cities Regions"]
    if "City" in df.columns:
        df = df.drop(columns=["City"])
        excel_sheets["Instagram Top Cities Regions"] = df
        print("Removed 'City' column from 'Instagram Top Cities Regions' sheet.\n")

for sheet_name, df in excel_sheets.items():
    if "RowHash" in df.columns:
        df = df.drop(columns=["RowHash"])
        excel_sheets[sheet_name] = df
        print(f"Removed 'RowHash' column from sheet: {sheet_name}\n")

if "Instagram Post Engagement" in excel_sheets:
    df = excel_sheets["Instagram Post Engagement"]
    if "Media ID" in df.columns:
        df = df.drop(columns=["Media ID"])
        excel_sheets["Instagram Post Engagement"] = df
        print("Dropped 'Media ID' column from 'Instagram Post Engagement' sheet.\n")

output_folder = "dataset"
for sheet_name, df in excel_sheets.items():
    output_path = os.path.join(output_folder, f"{sheet_name}.csv")
    df.to_csv(output_path, index=False)
    print(f"Exported sheet '{sheet_name}' to {output_path}\n")






