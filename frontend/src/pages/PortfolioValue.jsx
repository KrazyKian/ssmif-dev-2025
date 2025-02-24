import React, { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

const API_BASE_URL = "http://localhost:8000";

const PortfolioValue = () => {
  const [portfolioData, setPortfolioData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/portfolio_value`)
      .then((response) => {
        const formattedData = response.data.map(entry => ({
          date: new Date(entry.date).toISOString().split("T")[0],
          value: Number(entry.value)
        }));
        setPortfolioData(formattedData);
      })
      .catch((error) => {
        console.error("Error fetching portfolio value:", error);
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
      <h2 style={{ textAlign: "center" }}>Portfolio Holding Value Over Time</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={portfolioData}
          margin={{ top: 20, right: 50, left: 50, bottom: 50 }} // Increased margins
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" angle={-45} textAnchor="end" tickFormatter={(date) => new Date(date).toLocaleDateString()} />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={3} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PortfolioValue;
