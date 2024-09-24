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


# Read from nyse.csv
with open("sp500.csv", encoding="utf-8") as file:
    csv = reader(file)
    companies = list(csv)[1:]  # Skip header

# Create the Output folder if it doesn't exist
output_dir = "Output"
if not path.exists(output_dir):
    mkdir(output_dir)

for company in track(companies):
    cik = pad_cik(company[6]) 
    company_dir = f"{output_dir}/{company[1]}"
    
    # Create a directory for the company if it doesn't exist
    if not path.exists(company_dir):
        mkdir(company_dir)
    
    try:
        submissions = getSubmissionsByCik(cik)
        selected = [sub for sub in submissions if sub.form == "10-K"]

        print(f"Found {len(selected)} 10-K for {company[0]}")

        downloads = []
        missed = 0
        for submission in selected:
            try:
                downloads.append(getXlsxUrl(cik, submission.accessionNumber))
            except FileNotFoundError:
                missed += 1
                continue

        print(f"{len(downloads)} reports to be downloaded for {cik} [missed {missed}]")
        
        total = len(downloads)
        done = 0
        for downloadUrl in downloads:
            download(downloadUrl, f"{company_dir}/{downloadUrl.split('/')[-2]}.xlsx")
            done += 1
            print(f"Downloaded [{done}/{total}]")

    except InvalidCIK:
        print(f"Failed for {company[0]} ({cik})")
        continue
