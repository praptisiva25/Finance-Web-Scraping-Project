import pandas as pd
from os import path, listdir, makedirs
from csv import reader

# Define paths
input_dir = "C://Users//prapt//OneDrive//Desktop//OutputV"  # Directory where the individual files are located
csv_file_path = "C://Users//prapt//OneDrive//Desktop//sp500.csv"  # Path to the sp500.csv file
merged_dir = "C://Users//prapt//OneDrive//Desktop//Merged_FilesFinal"  # Directory to store merged files

# Create the merged directory if it doesn't exist
if not path.exists(merged_dir):
    makedirs(merged_dir)

# Read company names from sp500.csv
with open(csv_file_path, encoding="utf-8") as file:
    csv_reader = reader(file)
    companies = [row[1] for row in list(csv_reader)[1:]]  # Extract company names (assuming they are in the second column)

# Function to merge all files of a certain type for a given company
def merge_files(company_name, file_type_prefix):
    company_dir = f"{input_dir}//{company_name}"

    # Ensure the company directory exists
    if not path.exists(company_dir):
        print(f"Directory for {company_name} does not exist. Skipping...")
        return

    # Get all files that match the file type prefix (balance sheet or income statement)
    files = [f for f in listdir(company_dir) if f.startswith(file_type_prefix) and f.endswith(".csv")]
    files.sort()  # Sort the files based on their names (assumed to follow a logical order like _1, _2, etc.)

    # Check if there are enough files
    if len(files) < 2:
        print(f"Not enough files to merge for {file_type_prefix} in {company_name}. At least 2 files required.")
        return

    # Start with the first file as the base file (all columns will be retained)
    base_file = pd.read_csv(f"{company_dir}/{files[0]}")
    print(f"Starting with base file: {files[0]}")

    # Loop through the rest of the files and append their columns (excluding the first column)
    for idx, file in enumerate(files[1:], start=2):  # Start index from 2 to indicate file number
        temp_file = pd.read_csv(f"{company_dir}/{file}")
        
        # Make sure the file has more than one column to append
        if temp_file.shape[1] < 2:
            print(f"File {file} doesn't have enough columns. Skipping...")
            continue

        # Append all columns from the temp file except the first column (which is usually the index or identifier)
        for col in temp_file.columns[1:]:
            new_col_name = f"{col}_file{idx}"  # Make column names unique by appending the file number
            base_file[new_col_name] = temp_file[col]
        
        print(f"Appended columns from {file}. Current shape: {base_file.shape}")

    # Save the merged file in the company-specific folder within the merged directory
    company_merged_dir = f"{merged_dir}/{company_name}"
    if not path.exists(company_merged_dir):
        makedirs(company_merged_dir)

    # Output filename logic
    if file_type_prefix == "Consolidated_Statement_of_Income":
        output_file = f"{company_merged_dir}/Consolidated_Statements_of_Income_all_years_{company_name}.csv"
    elif file_type_prefix == "Consolidated_Balance_Sheet":
        output_file = f"{company_merged_dir}/Consolidated_Balance_Sheet_all_years_{company_name}.csv"

    # Save the merged file
    base_file.to_csv(output_file, index=False)
    print(f"Saved merged file to {output_file}")

# Append columns for each company from the sp500.csv list
for company in companies:
    # Append columns for the income statement files
    merge_files(company, "Consolidated_Statement_of_Income")
    
    # Append columns for the balance sheet files
    merge_files(company, "Consolidated_Balance_Sheet")
