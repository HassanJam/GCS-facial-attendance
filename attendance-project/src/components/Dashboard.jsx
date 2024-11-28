import React, { useState } from "react";
import { toast, ToastContainer } from "react-toastify";
import UpdateEncoding from "./UpdateEncoding";

const Dashboard = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [password, setPassword] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const adminPassword = "admin123";

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === adminPassword) {
      setIsAuthenticated(true);
    } else {
      toast.error("Incorrect admin password!");
    }
  };

  return (
    <div className="flex flex-col justify-center items-center min-h-screen bg-red-50 p-4">
      {/* Ask if the user is an admin */}
      {!isAdmin && !isAuthenticated && (
        <div className="bg-white p-6 rounded-lg shadow-md max-w-md w-full mb-4 text-center">
          <p className="text-xl font-semibold mb-4">Are you an admin?</p>
          <button
            onClick={() => setIsAdmin(true)}
            className="bg-red-600 text-white px-6 py-2 rounded-full hover:bg-red-700 transition duration-300"
          >
            Yes, I am an admin
          </button>
        </div>
      )}

      {/* If the user confirms they are an admin, ask for the admin password */}
      {isAdmin && !isAuthenticated && (
        <form
          onSubmit={handleLogin}
          className="bg-white p-6 rounded-lg shadow-md max-w-md w-full"
        >
          <p className="text-xl font-semibold mb-4">Enter Admin Password</p>
          <input
            type="password"
            placeholder="Admin Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="border border-gray-300 rounded-lg p-3 mb-4 w-full text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
            required
          />
          <button
            type="submit"
            className="bg-red-600 text-white px-6 py-2 rounded-full w-full hover:bg-red-700 transition duration-300"
          >
            Submit
          </button>
        </form>
      )}

      {/* Toast notification container */}
      <ToastContainer />

      {/* Show the main content once authenticated */}
      {isAuthenticated && (
        <div className="w-full max-w-md mt-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <UpdateEncoding />
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
