import numpy as np
import mysql.connector
from datetime import datetime, timedelta
import cv2
import face_recognition
from checkinimutil import WebCamVideoStream,FPS
import time
def get_db_connection():
    """Establish and return a connection to the MySQL database."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="cms"
        )
    except mysql.connector.Error as e:
        print(f"Database connection failed: {e}")
        exit(1)

def today_attendance(cursor, mydb, employee_id, log_time):
    try:
        date = log_time.date()
        check_query = "SELECT time_in, time_out FROM employee_management_attendance WHERE employee_id=%s AND date=%s"
        cursor.execute(check_query, (employee_id, date))
        
        attendance_record = cursor.fetchone()

        if not attendance_record:  # No record for the day
            print("hours",log_time.hour)
            if log_time.hour > 11:  # If time-in is before 11 AM
                print(f"Cannot log time-in for employee {employee_id} before 11:00 AM.")
                sql = '''
                INSERT INTO employee_management_attendance 
                (employee_id, date, time_in, status, comments, hours_worked, is_overtime,Location)
                VALUES (%s, %s, %s, %s, %s, NULL, 0,%s)
            '''
                val = (employee_id, date, log_time.time(), "late", "Logged late in","office")
                cursor.execute(sql, val)
                mydb.commit()
                return 'in'
            sql = '''
                INSERT INTO employee_management_attendance 
                (employee_id, date, time_in, status, comments
                , hours_worked, is_overtime,Location)
                VALUES (%s, %s, %s, %s, %s, NULL, 0,"office")
            '''
            val = (employee_id, date, log_time.time(), "present", "Logged in")
            cursor.execute(sql, val)
            mydb.commit()
            print(f"Time-in logged for employee {employee_id} at {log_time}.")
            return 'in'
        else:
            time_in, time_out = attendance_record
            if time_in is not None:
                # Ensure time_in is of type datetime.time() before combining
                if isinstance(time_in, timedelta):
                    time_in = (datetime.min + time_in).time()
                
                if not time_out:  # If time-out is not recorded
                    # Ensure time_in_datetime is set
                    time_in_datetime = datetime.combine(date, time_in)
                    time_diff = log_time - time_in_datetime
                    
                    if time_diff.total_seconds() >= 60:  # If 1 minute has passed
                        worked = (log_time - time_in_datetime).total_seconds() / 3600  # Hours worked
                        overtime = max(0, worked - 8)

                        update_query = '''
                            UPDATE employee_management_attendance
                            SET time_out = %s, hours_worked = %s, is_overtime = %s
                            WHERE employee_id = %s AND date = %s
                        '''
                        cursor.execute(update_query, (log_time.time(), worked, overtime, employee_id, date))
                        mydb.commit()
                        print(f"Time-out updated for employee {employee_id} at {log_time}.")
                        return 'out'
                    else:
                        print(f"Cannot update time-out for employee {employee_id} until 1 minute has passed since time-in.")
                else:
                    # Set time_in_datetime if time_in is not None
                    time_in_datetime = datetime.combine(date, time_in)
                    worked = (log_time - time_in_datetime).total_seconds() / 3600  # Hours worked
                    overtime = max(0, worked - 8)

                    update_query = '''
                            UPDATE employee_management_attendance
                            SET time_out = %s, hours_worked = %s, is_overtime = %s
                            WHERE employee_id = %s AND date = %s
                        '''
                    cursor.execute(update_query, (log_time.time(), worked, overtime, employee_id, date))
                    mydb.commit()
                    print(f"Updating Time-out for employee {employee_id}.")
                    return 'out'
                    
            else:
                print(f"Time-in is missing for employee {employee_id}.")
    except mysql.connector.errors.DatabaseError as e:
        if e.errno == 1412:  # Table definition changed
            print(f"Database error (table changed): {e}")
            # Reconnect to the database
            mydb = get_db_connection()
            cursor = mydb.cursor()
            print("Reconnected to the database.")
            # Retry the query
            today_attendance(cursor, mydb, employee_id, log_time)
        else:
            raise


def reconnect_database(mydb, cursor):
    """Reconnect to the database."""
    print("Reconnecting to the database...")
    mydb.close()
    mydb = get_db_connection()
    cursor.close()
    cursor = mydb.cursor()
    return mydb, cursor

def log_raw_data(cursor, mydb, employee_id, log_time,log_type):
    """Log raw attendance data."""
    
    # first check if employee record exists in the database limit 1 desc
    
    #cursor.execute("SELECT * FROM employee_management_employee WHERE id=%s", (employee_id,))

    
    
    try:
        query = '''
            INSERT INTO rawdata (employee_id, log_type, log_time, date)
            VALUES (%s, %s, %s, %s)
        '''

        values = (employee_id, log_type, log_time, log_time.date())
        cursor.execute(query, values)
        mydb.commit()
        print(f"Raw data logged for employee {employee_id} at {log_time}.")
    except mysql.connector.Error as e:
        print(f"Error logging raw data: {e}")

def load_known_encodings(cursor):
    """Load and parse face encodings from the database."""
    employee_encodings = {}
    try:
        query = "SELECT EmployeeID, Encoding FROM Encodings"
        cursor.execute(query)
        employees_data = cursor.fetchall()

        for employee_id, encodings in employees_data:
            try:
                encoding_arrays = [
                    np.fromstring(enc.strip(), sep=',') for enc in encodings.strip('[]').split('], [')
                ]
                employee_encodings[employee_id] = [enc for enc in encoding_arrays if enc.shape == (128,)]
            except Exception as e:
                print(f"Error parsing encoding for EmployeeID {employee_id}: {e}")
    except mysql.connector.Error as e:
        print(f"Error loading encodings: {e}")
    return employee_encodings

def process_camera_frame(cursor, mydb, img, employee_encodings):
    """Process a single camera frame and detect faces."""
    img_small = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
    img_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)

    face_current_frame = face_recognition.face_locations(img_small)
    encode_current_frame = face_recognition.face_encodings(img_small, face_current_frame)

    for encode_face, face_location in zip(encode_current_frame, face_current_frame):
        best_distance = float('inf')
        employee_id_best = None

        for employee_id, known_encodings in employee_encodings.items():
            for known_encoding in known_encodings:
                face_distance = face_recognition.face_distance([known_encoding], encode_face)[0]
                if face_distance < best_distance:
                    best_distance = face_distance
                    employee_id_best = employee_id

        if best_distance < 0.38:
            current_time = datetime.now()
            log_type= today_attendance(cursor, mydb, employee_id_best, current_time)
            log_raw_data(cursor, mydb, employee_id_best, current_time,log_type)

            # Draw rectangle and add label for the recognized face
            top, right, bottom, left = face_location
            top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(img, f"ID: {employee_id_best}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
        else:
            print("Unknown face detected.")

    return img


def mark_absent_employees(cursor, mydb, current_date):
    cursor.execute("SELECT id FROM employee_management_employee")  
    all_employees = cursor.fetchall()

    for (employee_id,) in all_employees:
        # Check if there is a time_in record for today
        check_query = "SELECT time_in FROM employee_management_attendance WHERE employee_id=%s AND date=%s"
        cursor.execute(check_query, (employee_id, current_date))
        
        # Fetch attendance record
        attendance_record = cursor.fetchall()

        if not attendance_record or attendance_record[0][0] is None:  # No time_in record
            # Check if the employee is already marked as absent
            absent_check_query = "SELECT * FROM employee_management_attendance WHERE employee_id=%s AND date=%s AND status='absent'"
            cursor.execute(absent_check_query, (employee_id, current_date))
            mydb.commit()
            absent_record = cursor.fetchall()

            if not absent_record:  # If no absence record exists
                # If there's no time_in record, mark as absent
                sql = '''
                    INSERT INTO employee_management_attendance 
                    (employee_id, date, time_in, status, comments, hours_worked, is_overtime)
                    VALUES (%s, %s, NULL, %s, %s, NULL, 0)
                '''
                val = (employee_id, current_date, "absent", "No log-in recorded")  # Store as NULL for time_in
                cursor.execute(sql, val)
                mydb.commit()
                print(f"Marked employee {employee_id} as absent for {current_date}.")  
def cleanupdata(cursor, current_date):
    daybeforeyesterday = current_date - timedelta(days=2)
    query = "DELETE FROM rawdata WHERE date<=%s"
    cursor.execute(query, (daybeforeyesterday,))
    print("Attendance data for", daybeforeyesterday, "has been deleted")
    
    
def mark_late_employees(cursor, mydb, current_date):
    print("Marking late employees")
    cursor.execute("SELECT id FROM employee_management_employee")  
    mydb.commit()
    all_employees = cursor.fetchall()

    for (employee_id,) in all_employees:
        # Check if there is a time_in record for today
        check_query = "SELECT time_in FROM employee_management_attendance WHERE employee_id=%s AND date=%s"
        cursor.execute(check_query, (employee_id, current_date))
        
        # Fetch attendance record
        attendance_record = cursor.fetchall()

        if attendance_record and attendance_record[0][0] is not None:  # If there is a time_in record
            time_in = attendance_record[0][0]
            
            # Check if the time_in is after 11:00 AM
            # Check if the employee is already marked as late
            late_check_query = "SELECT * FROM employee_management_attendance WHERE employee_id=%s AND date=%s AND status='late'"
            cursor.execute(late_check_query, (employee_id, current_date))
            late_record = cursor.fetchall()
            mydb.commit()

            if not late_record:  # If no late record exists
                print("Marking")
                # If time_in is after 11 AM, mark as late
                sql = '''
                    INSERT INTO employee_management_attendance 
                    (employee_id, date, time_in, status, comments, hours_worked, is_overtime)
                    VALUES (%s, %s, %s, %s, %s, NULL, 0)
                '''
                val = (employee_id, current_date, time_in, "late", "Logged in after 11:00 AM")  # Store actual time_in
                cursor.execute(sql, val)
                mydb.commit()
                print(f"Marked employee {employee_id} as late for {current_date} (Logged in after 11:00 AM).")



import cv2
import numpy as np
import face_recognition
from typing import Tuple

def match_face_from_picture(image) -> Tuple[str, int]:
    """Matches a face from the given picture (image) with the encodings stored in the database."""
    mydb = get_db_connection()
    cursor = mydb.cursor()
    employee_id_best = None  # Initialize to avoid NameError
    try:
        # Validate the image
        if image is None:
            print("Error: The image is not loaded correctly (None).")
            return "Failure", employee_id_best

        if not isinstance(image, (np.ndarray, np.generic)):
            print("Error: The image is not a valid NumPy array.")
            return "Failure", employee_id_best

        if len(image.shape) != 3:
            print(f"Error: The image has an invalid shape: {image.shape}. It should be 3-dimensional.")
            return "Failure", employee_id_best

        # Resize the image
        try:
            img_small = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
        except Exception as e:
            print(f"Error in resizing the image: {e}")
            return "Failure", employee_id_best

        # Convert to RGB
        img_rgb = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)

        # Find face locations and encodings
        face_locations = face_recognition.face_locations(img_rgb)
        face_encodings = face_recognition.face_encodings(img_rgb, face_locations)

        if not face_encodings:
            print("No faces detected in the image.")
            return "Failure", employee_id_best

        # Load known encodings
        employee_encodings = load_known_encodings(cursor)
        best_distance = float('inf')

        # Compare detected faces with known encodings
        for encode_face in face_encodings:
            for employee_id, known_encodings in employee_encodings.items():
                for known_encoding in known_encodings:
                    face_distance = face_recognition.face_distance([known_encoding], encode_face)[0]
                    if face_distance < best_distance:
                        best_distance = face_distance
                        employee_id_best = employee_id

        # Threshold check
        if best_distance < 0.38:
            print(f"Match found for employee {employee_id_best} with distance {best_distance:.2f}")
            return "Success", employee_id_best

        print("No matching face found.")
        return "Failure", employee_id_best

    except Exception as e:
        print(f"Error in matching face from picture: {e}")
        return "Failure", employee_id_best


def start_stream(url):
    video_stream = WebCamVideoStream(url).start()
    fps = FPS().start()
    return video_stream, fps

def main():
    """Main function to run the attendance system."""
    mydb = get_db_connection()
    cursor = mydb.cursor()

    # Load encodings
    employee_encodings = load_known_encodings(cursor)
    url = "rtsp://admin:Admin123@192.168.0.212:554/channel/1"

    cap, fps = start_stream(url)
    fps.update()

    refresh_interval = 60
    last_check_time = datetime.now()

    # Set window name and dimensions
    window_name = "Attendance Camera"
    screen_width = 1280  # Desired width
    screen_height = 720  # Desired height
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  
    cv2.resizeWindow(window_name, screen_width, screen_height)

    while True:
        current_time = datetime.now()
        current_date = current_time.date()

        success, img = cap.read()
        if not success:
            print("Attempting to reconnect...")
            cap.stop()  # Use the stop method
            time.sleep(1)
            cap, fps = start_stream(url)  # Reinitialize stream
            continue
        if success:
            img = process_camera_frame(cursor, mydb, img, employee_encodings)
            
            # Resize the frame to fit the desired window dimensions
            img = cv2.resize(img, (screen_width, screen_height))
            cv2.imshow(window_name, img)

        # Refresh known encodings every minute
        if (datetime.now() - last_check_time).total_seconds() >= refresh_interval:
            employee_encodings = load_known_encodings(cursor)
            last_check_time = datetime.now()

        if current_time.hour == 16 and 17 <= current_time.minute <= 20:
            mark_absent_employees(cursor, mydb, current_date)
            cleanupdata(cursor, current_date)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    fps.stop()
    cursor.close()
    mydb.close()


if __name__ == "__main__":
    main()