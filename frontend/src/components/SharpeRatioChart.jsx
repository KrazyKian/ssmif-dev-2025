import React, { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const SharpeRatioChart = () => {
  const [sharpeData, setSharpeData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/sharpe_ratio`)
      .then((response) => {
        setSharpeData(response.data);
      })
      .catch((error) => {
        console.error("Error fetching Sharpe ratio:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <h2>Loading Sharpe Ratio Data...</h2>;
  }

  return (
    <div style={{ width: "90vw", height: "400px", padding: "20px", margin: "0 auto" }}>
      <h2 style={{ textAlign: "center" }}>Sharpe Ratio Over Time</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sharpeData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={["auto", "auto"]} />
          <Tooltip />
          <Line type="monotone" dataKey="sharpe_ratio" stroke="#8884d8" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SharpeRatioChart;
