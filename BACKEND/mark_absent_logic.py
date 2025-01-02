import time
from datetime import datetime, timedelta
import mysql.connector
def get_db_connection():
    """Establish and return a connection to the MySQL database."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678",
            database="cms"
        )
    except mysql.connector.Error as e:
        print(f"Database connection failed: {e}")
        exit(1)

import time
from datetime import datetime, timedelta

def run_at_midnight(task_func):
    """Runs the given task function at 5:07 PM every day."""
    # while True:
    # Get the current time
    # Get the current time without microseconds
    now = datetime.now().replace(microsecond=0)
    print(f"Current time: {now}")

    # Define the target time without microseconds
    target_time = datetime(now.year, now.month, now.day, 18, 44, 30)  # 5:55 PM today

    
    # If it's already past 5:07 PM, set the target to 5:07 PM tomorrow
    if now > target_time:
        target_time = datetime(now.year, now.month, now.day, 17, 38, 0) + timedelta(days=1)

    print(f"Target time: {target_time}")

    if now == target_time:
    
        time_until_target = (target_time - now).total_seconds()
        
        print(f"Waiting {time_until_target} seconds until 5:07 PM...")
        # time.sleep(time_until_target)  # Wait until 5:07 PM
        
        # Run the task at 5:07 PM
        print(f"Task started at: {datetime.now()}")

        task_func()
        print('Sleep started')
        time.sleep(1)
        print('Sleep ended')


        
        
def mark_employee_absent(employee_id):
    """Marks the given employee as absent for the current day."""
    query = f"INSERT INTO employee_management_attendance (employee_id, date, status, comments, is_overtime) VALUES ({employee_id}, CURDATE(), 'absent', 'initial absent', 0)"
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
