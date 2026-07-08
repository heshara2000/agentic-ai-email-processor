from pydantic import BaseModel

class EmployeeData(BaseModel):
    employee_name: str
    email: str
    department: str
    manager: str
    office: str
    start_date: str