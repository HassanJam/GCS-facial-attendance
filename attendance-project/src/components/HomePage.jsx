import React, { useState, useEffect } from "react";
import axios from "axios";
import logo from "../assets/gcs.png";
import AttendanceTable from "./AttendanceTable";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { AiOutlineReload } from "react-icons/ai";
import Navbar from "./Navbar";
import backgroundImage from "../assets/background.jpg"; // Path to your background image

const api = "http://127.0.0.1:8001";

const HomePage = () => {
  const [records, setRecords] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState({});
  const [lastLog, setLastLog] = useState({});
  const [selectedTab, setSelectedTab] = useState("live");

  useEffect(() => {
    if (selectedTab === "live") {
      fetchTodayLogs();
      fetchLastLog();
      const intervalId = setInterval(() => {
        fetchLastLog();
      }, 2000);

      return () => clearInterval(intervalId);
    }
  }, [selectedTab, lastLog]);

  const fetchTodayLogs = async () => {
    try {
      const response = await axios.get(`${api}/today_logs/`);
      setRecords(response.data);
    } catch (error) {
      console.error("Error fetching today logs:", error);
      toast.error("Error fetching today logs");
    }
  };

  const fetchLastLog = async () => {
    try {
      const response = await axios.get(`${api}/last_log/`);
      const newLog = response.data;
      if (
        lastLog.employee_id !== newLog.employee_id ||
        lastLog.log_time !== newLog.log_time
      ) {
        setLastLog(newLog);
        setModalContent(newLog);
        setIsModalOpen(true);
      }
    } catch (error) {
      console.error("Error fetching last log:", error);
    }
  };

  const handleReload = () => {
    fetchTodayLogs();
  };

  return (
    <div
      className="min-h-screen flex flex-col justify-between"
      style={{
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {/* Main Content */}
      <main className="flex flex-col items-center w-full px-6 py-12 space-y-8">
        {/* Header */}
        <header className="flex flex-col items-center space-y-4">
          <h1 className="text-4xl font-semibold text-white">GCS Attendance System</h1>
          <p className="text-lg text-gray-600">Manage and view attendance in real-time</p>
        </header>

        {/* Tabs */}
        <div className="flex justify-start space-x-6 text-lg">
          <button
            onClick={() => setSelectedTab("live")}
            className={`py-3 px-8 rounded-lg font-bold ${
              selectedTab === "live"
                ? "bg-red-500 text-white"
                : "bg-transparent hover:bg-red-200 text-white"
            } transition-all duration-300`}
          >
            Live
          </button>
          <button
            onClick={() => setSelectedTab("table")}
            className={`py-3 px-8 rounded-lg font-bold ${
              selectedTab === "table"
                ? "bg-red-500 text-white"
                : "bg-transparent hover:bg-red-200 text-white"
            } transition-all duration-300`}
          >
            Table
          </button>
        </div>

        {/* Content based on selected tab */}
        {selectedTab === "live" && (
          <div className="space-y-6 w-full max-w-5xl bg-white rounded-xl p-8 shadow-lg">
            <h2 className="text-2xl font-semibold text-gray-700 text-center">
              Live Attendance Log
            </h2>

            {/* Modal for new attendance log */}
            {isModalOpen && (
              <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
                <div className="bg-white p-8 rounded-xl shadow-xl w-full max-w-3xl animate-fadeIn">
                  <h3 className="text-3xl font-semibold text-gray-700 mb-6 text-center">
                    New Attendance Log
                  </h3>
                  <div className="flex items-center space-x-8">
                    <div className="flex-shrink-0">
                      <img
                        src={`${api}${modalContent.employee_image}`}
                        alt="Employee"
                        className="w-52 h-52 object-cover rounded-full border-4  shadow-lg"
                      />
                    </div>
                    <div className="space-y-4">
                      <p className="text-lg text-gray-800">
                        <strong>Employee ID:</strong> {modalContent.employee_id}
                      </p>
                      <p className="text-lg text-gray-800">
                        <strong>Log Time:</strong> {modalContent.log_time}
                      </p>
                      <p className="text-lg text-gray-800">
                        <strong>Employee Name:</strong> {modalContent.employee_name}
                      </p>
                    </div>
                  </div>
                  <div className="flex justify-center mt-8">
                    <button
                      onClick={() => setIsModalOpen(false)}
                      className="bg-red-500 text-white py-3 px-12 rounded-xl hover:bg-red-600 transition-all duration-300"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === "table" && (
          <div className="w-full max-w-6xl bg-white rounded-xl p-8 shadow-lg">
            <h2 className="text-2xl font-semibold text-gray-700 text-center">
              Attendance Logs
            </h2>
            <AttendanceTable records={records} />
          </div>
        )}
      </main>

      {/* Reload Button */}
      {selectedTab === "table" && (
        <div className="flex justify-center mt-8">
          <button
            onClick={handleReload}
            className="flex items-center text-lg bg-red-500 text-white py-3 px-8 rounded-xl hover:bg-red-600 transition-all duration-300"
          >
            <AiOutlineReload size={24} className="mr-2" />
            Reload Data
          </button>
        </div>
      )}

      {/* Toast Notifications */}
      <ToastContainer />
    </div>
  );
};

export default HomePage;
