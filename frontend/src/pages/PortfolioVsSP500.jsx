import React, { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from "recharts";

const API_BASE_URL = "http://localhost:8000";

const PortfolioVsSP500 = () => {
  const [performanceData, setPerformanceData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/portfolio_performance`)
      .then((response) => {
        console.log("Raw API Data:", response.data);
        const formattedData = response.data.map(entry => ({
          date: new Date(entry.date).toISOString().split("T")[0], // Ensure date is a string
          portfolio: Number(entry.portfolio), // Ensure numbers
          sp500: Number(entry.sp500),
        }));
        console.log("Formatted Data:", formattedData);
        setPerformanceData(formattedData);
      })
      .catch((error) => {
        console.error("Error fetching performance data:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
        <div style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "80vh",
          width: "100%",
          textAlign: "center",
        }}>
          <h2>Loading portfolio data...</h2>
        </div>
      );
  }

  return (
    <div style={{ width: "90vw", height: "80vh", padding: "20px", margin: "0 auto" }}>
      <h2 style={{ textAlign: "center" }}>Portfolio Performance vs. S&P 500</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={performanceData} margin={{ top: 20, right: 50, left: 50, bottom: 50 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" angle={-45} textAnchor="end" tickFormatter={(date) => new Date(date).toLocaleDateString()} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="portfolio" stroke="#ff7300" strokeWidth={3} name="Portfolio" />
          <Line type="monotone" dataKey="sp500" stroke="#387908" strokeWidth={3} name="S&P 500" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PortfolioVsSP500;
