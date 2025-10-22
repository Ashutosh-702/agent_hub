import re


def extract_departments_from_config(config_string):
    # Extract the departments line
    dept_match = re.search(r'Department\(s\) of people to be searched: (.+)', config_string)
    if dept_match:
        departments_str = dept_match.group(1)
        # Split by comma and clean up
        departments = [dept.strip() for dept in departments_str.split(',')]
        return departments
    return []