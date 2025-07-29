import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os


def upload_company_name_to_sheets(company_data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    base_dir =os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    creds = ServiceAccountCredentials.from_json_keyfile_name(f"{base_dir}/config/service_account.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/13XUGl8aoElnlDVjd3iZKHzpENH8wZkX3l-N0WVFsZUo/edit?gid=0#gid=0")
    for company_name in company_data:
        sheet = spreadsheet.sheet1
        sheet.append_row([company_name])
        print(f"Uploaded company name: {company_name}")

def upload_company_name_to_csv(company_data):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    csv_file_path = f"{base_dir}/data/company_names.csv"
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
    with open(csv_file_path, 'w+') as file:
        file.write("Company_name\n")
        for company_name in company_data:
            file.write(f"{company_name}\n")
            print(f"Uploaded company name to CSV: {company_name}")

def update_history(company_data, query):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    counter_file = f"{base_dir}/core_sdr/history/counter.txt"
    os.makedirs(os.path.dirname(counter_file), exist_ok=True)
    if not os.path.exists(counter_file):
        with open(counter_file, 'w') as f:
            f.write("0")
    with open(counter_file, 'r+') as f:
        f.seek(0)
        content = f.read().strip()
        if content!='' and content.isdigit():
            run_number = int(content) + 1
            print(f"Incremented run number to: {run_number}")
        else:
            run_number = 1
        f.seek(0)
        f.write(str(run_number))
        f.truncate()
    run_number = str(run_number).zfill(4)
    history_file_path = f"{base_dir}/core_sdr/history/history_{run_number}/history.log"
    os.makedirs(os.path.dirname(history_file_path), exist_ok=True)
    with open(history_file_path, 'w') as file:
        file.write(f"Query: {query}\n")
        file.write("Companies:\n")
        for company_name in company_data:
            file.write(f"- {company_name}\n")
        print(f"Updated history with query: {query} and companies: {company_data}"  )