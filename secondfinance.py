import pandas as pd
from csv import reader
from os import mkdir, path
from edgarpython.exceptions import InvalidCIK
from edgarpython.secapi import getSubmissionsByCik, getXlsxUrl
from requests import get
from rich.progress import track

def download(url, filename):
    resp = get(
        url,
        headers={
            'User-Agent': 'PraptiSiva AdminContact@praptisivaahis@gmail.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        },
    )
    with open(filename, "wb") as file:
        file.write(resp.content)

def pad_cik(cik):
    """Pad CIK with leading zeros to make it 10 digits long."""
    return cik.zfill(10)

# Define possible sheet name variations for income statement and balance sheet
possible_income_sheet_names = [
    'consolidated statement of incom',
    'consolidated statements of incom',
    'consolidated statement of income',
    'consolidated statements of income',
    'consolidated statement of earning',
    'consolidated statement of earnings',
    'consolidated statements of earning',
    'consolidated statements of earnings',
    'statement of operations',
    'consolidated statement of earn',
    'consolidated statements of earn',
    'consolidated statement of ear',
    'consolidated statements of ear',
    'consolidated statement of earni',
    'consolidated statements of earni',
    'consolidated income statement',
    'consolidated income statements',
    'consolidated statement of inco',
    'consolidated statements of inco',
    'consolidated statement of oper',
    'consolidated statements of oper',
    'consolidated statement of ope',
    'consolidated statements of ope',
    'consolidated statement of comp',
    'consolidated statements of comp',
    'consolidated statement of com',
    'consolidated statements of com',
    'consolidated statements of co',
    'consolidated statements of co',
     'consolidated statement of inc',
    'consolidated statements of inc',
     'consolidated statement of in',
    'consolidated statements of in',
     'consolidated statement of op',
    'consolidated statements of op',
    'statement of consolidated opera',
    'statements of consolidated opera',
    'statement of consolidated oper',
    'statements of consolidated oper',
    'statement of consolidated operations',
    'statements of consolidated operations',
     
]

possible_balance_sheet_names = [
    'consolidated balance sheet',
    'consolidated balance sheets',
    'balance sheet',
     'consolidated statement of fin',
    'consolidated statements of fin',
     'consolidated statement of financial',
    'consolidated statements of financial',
]

# Read from sp500.csv
with open("sp500.csv", encoding="utf-8") as file:
    csv = reader(file)
    companies = list(csv)[1:]  # Skip header row

# Create output directory if it doesn't exist
output_dir = "OutputV"
if not path.exists(output_dir):
    mkdir(output_dir)

for company in track(companies):
    cik = pad_cik(company[6])  # Assuming CIK is in the seventh column (index 6)
    company_name = company[1]
    company_dir = f"{output_dir}/{company_name}"
    
    # Create a directory for the company if it doesn't exist
    if not path.exists(company_dir):
        mkdir(company_dir)
    
    try:
        # Get the 10-K submissions
        submissions = getSubmissionsByCik(cik)
        selected = [sub for sub in submissions if sub.form == "10-K"]

        print(f"Found {len(selected)} 10-K for {company[0]}")

        downloads = []
        for submission in selected:
            try:
                downloads.append(getXlsxUrl(cik, submission.accessionNumber))
            except FileNotFoundError:
                continue

        print(f"{len(downloads)} reports to be downloaded for {cik}")
        
        # Initialize counters for each company
        balance_sheet_counter = 1
        income_statement_counter = 1
        
        for downloadUrl in downloads:
            filename = f"{company_dir}/{downloadUrl.split('/')[-2]}.xlsx"
            download(downloadUrl, filename)
    
            try:
                xls = pd.ExcelFile(filename)
                
                # Extract and save consolidated income statement
                income_matching_sheet = None
                print(xls.sheet_names)
                for sheet_name in xls.sheet_names:
                    if any(term in (sheet_name.lower()).replace("_"," ") for term in possible_income_sheet_names):
                        print(sheet_name.lower())
                        income_matching_sheet = sheet_name
                        break

                if income_matching_sheet:
                    income_statement = pd.read_excel(xls, sheet_name=income_matching_sheet)
                    income_csv_path = f"{company_dir}/Consolidated_Statement_of_Income_{income_statement_counter}_{company_name}.csv"
                    income_statement.to_csv(income_csv_path, index=False)
                    print(f"Extracted Income Statement for {company[0]} to {income_csv_path}")
                    income_statement_counter += 1
                else:
                    print(f"No Income Statement found in {filename}")
                
            except Exception as e:
                print(f"Error processing income statement in {filename}: {e}")

            try:
                # Extract and save consolidated balance sheet
                balance_matching_sheet = None
                for sheet_name in xls.sheet_names:
                    if any(term in (sheet_name.lower()).replace("_"," ") for term in possible_balance_sheet_names):
                        balance_matching_sheet = sheet_name
                        break

                if balance_matching_sheet:
                    balance_sheet = pd.read_excel(xls, sheet_name=balance_matching_sheet)
                    balance_csv_path = f"{company_dir}/Consolidated_Balance_Sheet_{balance_sheet_counter}_{company_name}.csv"
                    balance_sheet.to_csv(balance_csv_path, index=False)
                    print(f"Extracted Balance Sheet for {company[0]} to {balance_csv_path}")
                    balance_sheet_counter += 1
                else:
                    print(f"No Balance Sheet found in {filename}")

            except Exception as e:
                print(f"Error processing balance sheet in {filename}: {e}")

    except InvalidCIK:
        print(f"Failed for {company[0]} ({cik})")
