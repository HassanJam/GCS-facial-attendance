import time
from datetime import datetime, timedelta
from gcs import get_db_connection

def run_at_midnight(task_func):
    """Runs the given task function at midnight every day."""
    while True:
        # Get the current time
        now = datetime.now()
        print(f"Current time: {now}")
        
        # Calculate the next midnight
        tomorrow = now + timedelta(days=1)
        next_midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        time_until_midnight = (next_midnight - now).total_seconds()
        
        print(f"Waiting {time_until_midnight} seconds until midnight...")
        time.sleep(time_until_midnight)  # Wait until midnight
        
        # Run the task at midnight
        print(f"Task started at: {datetime.now()}")
        task_func()
def mark_employee_absent(employee_id):
    """Marks the given employee as absent for the current day."""
    query = f"INSERT INTO employee_management_employee (employee_id, date, status) VALUES ({employee_id}, CURDATE(), 'absent')"
    print(f"Query: {query}")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    print(f"Employee {employee_id} marked as absent for today.")
    
    
def my_daily_function():
    print("Running my daily function...")
    query = "SELECT id FROM employee_management_employee"
    print(f"Query: {query}")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    employees = cursor.fetchall()
    print(f"Employees: {employees}")
    
    # Mark all employees as absent
    for employee in employees:
        employee_id = employee[0]
        print(f"Marking employee {employee_id} as absent...")
        mark_employee_absent(employee_id)
    

if __name__ == "__main__":
    run_at_midnight(my_daily_function)
