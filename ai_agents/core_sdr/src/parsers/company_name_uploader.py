import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os


def upload_company_name(company_data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    base_dir =os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    creds = ServiceAccountCredentials.from_json_keyfile_name(f"{base_dir}/config/service_account.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/13XUGl8aoElnlDVjd3iZKHzpENH8wZkX3l-N0WVFsZUo/edit?gid=0#gid=0")
    for company_name in company_data:
        sheet = spreadsheet.sheet1
        sheet.append_row([company_name])
        print(f"Uploaded company name: {company_name}")

