import logging
from typing import Optional
import cv2
import uvicorn
logging.basicConfig(level=logging.INFO)
import pydantic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect,Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr
from typing import List
from datetime import datetime, date, time, timedelta
import mysql.connector
import json
import os
import django
import face_recognition
from fastapi.staticfiles import StaticFiles
import numpy as np
from gcs import match_face_from_picture
from reverse_geocoding_test import reverse_geocode
app = FastAPI()
IMAGE_FOLDER = './images'
app.mount("/images", StaticFiles(directory=IMAGE_FOLDER), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost", user="root", password="12345678", database="cms"
    )

class AttendanceRecord(BaseModel):
    employee_id: int
    date: date
    log_time: time
    employee_name: str

class LogRequest(BaseModel):
    date: date

class PopupResponse(BaseModel):
    employee_id: int
    date: date
    log_time: time
    employee_name: str
    employee_image: str
    log_type: str
    

@app.get("/search_employee/")
async def search_employee(query: Optional[str] = None):
    try:
        if not query:
            return []

        mydb = get_db_connection()
        cursor = mydb.cursor()

        search_query = f"%{query}%"
        cursor.execute("""
            SELECT id, username, first_name, last_name 
            FROM employee_management_employee
            WHERE username LIKE %s 
            OR first_name LIKE %s 
            OR last_name LIKE %s 
            OR id LIKE %s
            LIMIT 10
        """, (search_query, search_query, search_query, search_query))

        employees = cursor.fetchall()
        result = [
            {"employee_id": emp[0], "username": emp[1], "first_name": emp[2], "last_name": emp[3]}
            for emp in employees
        ]

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/update_encoding/")
async def update_face_encoding(
    employee_id: Optional[int] = Form(None),
    username: Optional[str] = Form(None),
    profile_images: List[UploadFile] = File(...),
):
    try:
        if not employee_id and not username:
            raise HTTPException(status_code=400, detail="Employee ID or username is required.")

        mydb = get_db_connection()
        cursor = mydb.cursor()

        # Fetch employee by ID or username
        if employee_id:
            cursor.execute("SELECT id, username FROM employee_management_employee WHERE id = %s", (employee_id,))
        else:
            cursor.execute("SELECT id, username FROM employee_management_employee WHERE username = %s", (username,))
        
        employee = cursor.fetchone()

        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found.")
        
        employee_id = employee[0]
        employee_name = employee[1]

        # Create a directory for the employee if it doesn't exist
        employee_folder = os.path.join(IMAGE_FOLDER, str(employee_id))
        os.makedirs(employee_folder, exist_ok=True)

        # Process all uploaded images
        if profile_images:
            encodings = []
            for image_file in profile_images:
                # Generate a unique filename
                extension = image_file.filename.split('.')[-1]  # Get the file extension
                base_filename = f"{employee_id}"
                
                # Find the next available filename
                file_count = 0
                new_image_name = f"{base_filename}.{extension}"
                while os.path.exists(os.path.join(employee_folder, new_image_name)):
                    file_count += 1
                    new_image_name = f"{base_filename}_{file_count}.{extension}"

                # Save the image
                image_path = os.path.join(employee_folder, new_image_name)
                with open(image_path, "wb") as image_file_stream:
                    image_file_stream.write(await image_file.read())

                # Load and process the uploaded image for face recognition
                image = cv2.imread(image_path)
                if image is None:
                    raise HTTPException(status_code=400, detail="Uploaded image could not be read.")

                img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image_encodings = face_recognition.face_encodings(img_rgb)

                if image_encodings:
                    encodings.extend(image_encodings)

            if encodings:
                # Store the encodings in JSON format
                encodings_json = json.dumps([encoding.tolist() for encoding in encodings])

                # Check if encodings already exist for this employee
                encoding_query = "SELECT * FROM Encodings WHERE employeeid = %s"
                cursor.execute(encoding_query, (employee_id,))
                existing_encodings = cursor.fetchone()

                if existing_encodings:
                    # If encodings exist, update the existing record
                    update_query = """
                    UPDATE Encodings 
                    SET encoding = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE employeeid = %s
                    """
                    cursor.execute(update_query, (encodings_json, employee_id))
                else:
                    # If encodings do not exist, insert a new record
                    insert_query = """
                    INSERT INTO Encodings (employeeid, encoding)
                    VALUES (%s, %s)
                    """
                    cursor.execute(insert_query, (employee_id, encodings_json))

                mydb.commit()

                return {
                    "status": "Face encoding updated successfully for employee",
                    "employee_id": employee_id,
                    "employee_name": employee_name
                }
            else:
                raise HTTPException(status_code=400, detail="No faces detected in the uploaded images.")
        else:
            raise HTTPException(status_code=400, detail="No images were uploaded.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/today_logs/", response_model=List[AttendanceRecord])
def get_today_logs():
    current_date = datetime.now().date()
    try:
        mydb = get_db_connection()
        cursor = mydb.cursor()
        query = "SELECT employee_id, log_time FROM rawdata WHERE date=%s"
        cursor.execute(query, (current_date,))
        logs = cursor.fetchall()

        result = []
        for log in logs:
            employee_id = log[0]
            log_time = log[1]
            try:
                query3 = "SELECT username from employee_management_employee where id=%s"
                cursor.execute(query3, (employee_id,))
                userLog = cursor.fetchone()
                employee_name = userLog[0]
                if isinstance(log_time, timedelta):
                    log_time = (datetime.min + log_time).time()
                elif isinstance(log_time, time):
                    pass
                else:
                    logging.error(f"Unexpected log_time type: {type(log_time)}")
                    continue
                result.append(
                    {"employee_id": employee_id, "employee_name": employee_name, "date": current_date, "log_time": log_time}
                )
            except Exception as e:
                logging.error(f"Failed to fetch employee info: {str(e)}")
        return result
    except Exception as e:
        logging.error(f"Failed to fetch logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch logs")
def convert_image_to_numpy(image_bytes: bytes):
    """Convert bytes to a NumPy array image that OpenCV can process."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Decode image
    if image is None:
        raise ValueError("Failed to decode image")
    return image





@app.post("/app_attendance/")
async def mark_attendance(
    file: UploadFile = File(...),
    x: str = Form(..., description="X-coordinate as a string"),
    y: str = Form(..., description="Y-coordinate as a string"),
    log_type: str = Form(..., description="Log type as a string"),
    employeeid: int = Form(..., description="Employee ID as an integer")
):
    try:
        print("x:", x)
        print("y:", y)
        print("log_type:", log_type)

        # Read and convert the image
        image_bytes = await file.read()
        image = convert_image_to_numpy(image_bytes)

        # Call the match function with the image
        result, employee_id = match_face_from_picture(image)
        if employee_id == employeeid:
            print("result:", result)
            print("employee_id:", employee_id)

            if result == "Success":
                # Reverse geocode the coordinates to get the address
                address = reverse_geocode(float(x), float(y))
                print(f"The address for coordinates ({x}, {y}) is:\n{address}")

                # Get the current time and date
                current_time = datetime.now()
                current_date = current_time.date()
                print("current_date:", current_date)
                print("current_time:", current_time.time())
                    # Establish a database connection
                mydb = get_db_connection()
                cursor = mydb.cursor()

                # Step 1: Check if the employee already marked attendance for the day and log type
                check_query = """
                    SELECT COUNT(*) FROM employee_management_temp_appattendance
                    WHERE employee_id = %s AND date = %s AND log_type = %s
                """
                cursor.execute(check_query, (employee_id, current_date, log_type))
                result_count = cursor.fetchone()[0]

                if result_count > 0:
                    # If there's already an entry, return a message and skip insertion
                    cursor.close()
                    mydb.close()
                    return {"result": "Failure", "message": "Attendance for this employee has already been marked for today with this log type"}

                # Step 2: Insert the data into the database (only if no existing entry found)
                insert_query = """
                    INSERT INTO employee_management_temp_appattendance 
                    (employee_id, time, date, log_type, x_coordinate, y_coordinate, location_address, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
                """
                cursor.execute(insert_query, (
                    employee_id,
                    current_time.time(),
                    current_date,
                    log_type,
                    x,
                    y,
                    address
                ))

                # Commit the transaction
                mydb.commit()

                # Close the cursor and connection
                cursor.close()
                mydb.close()

                return {"result": "Attendance marked successfully", "employee_id": employee_id}

            else:
                return {"result": "Failure", "message": "No matching face found"}
        else:
            print("Unauthorized access")
            return {"result": "Failure", "message": "Employee ID does not match face"}

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Database error occurred while marking attendance")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while marking attendance")



@app.get("/last_log/", response_model=PopupResponse)
def get_last_log():
    current_date = datetime.now().date()
    try:
        mydb = get_db_connection()
        cursor = mydb.cursor()
        query = "SELECT employee_id, log_time,log_type FROM rawdata WHERE date=%s ORDER BY log_time DESC LIMIT 1"
        cursor.execute(query, (current_date,))
        log = cursor.fetchone()

        if log:
            employee_id = log[0]
            log_time = log[1]
            log_type = log[2]
            
            # Debug output
            print("Fetched log:", log)
            print("log_time type:", type(log_time))
            print("last_log_type :",log_type)
            # Fetch employee name
            query3 = "SELECT username from employee_management_employee where id=%s"
            cursor.execute(query3, (employee_id,))
            userLog = cursor.fetchone()
            employee_name = userLog[0]

            # Convert log_time (timedelta) to string format
            if isinstance(log_time, timedelta):
                total_seconds = int(log_time.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                log_time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            else:
                raise ValueError("Unexpected log_time type")

            # Find the last image for the employee
            employee_image = find_employee_image(employee_id) or ""  # Use empty string if None

            return {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "date": current_date,
                "log_time": log_time_str,
                "employee_image": employee_image,
                "log_type": log_type,
            }

        raise HTTPException(status_code=404, detail="No logs found for today")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch last log: {str(e)}")
   

    
def find_employee_image(employee_id: int) -> str:
    employee_folder = os.path.join(IMAGE_FOLDER, str(employee_id))
    # Check for supported image formats: jpg and png
    for extension in ['jpg', 'png']:
        image_path = os.path.join(employee_folder, f"{employee_id}.{extension}")
        if os.path.exists(image_path):
            return f"/images/{employee_id}/{employee_id}.{extension}"
    return None  # Return None if no image is found
      
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)