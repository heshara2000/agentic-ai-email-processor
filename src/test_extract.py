import glob
from nodes import extract_employee_data

for file_path in sorted(glob.glob("data/employee_*.pdf")):
    print("=" * 50)
    print("FILE:", file_path)
    print("=" * 50)
    result = extract_employee_data(file_path)
    print(result)
    print()