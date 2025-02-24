import React, { useEffect, useState } from "react";
import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const HoldingsTable = () => {
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/holdings`)
      .then((response) => {
        setHoldings(response.data);
      })
      .catch((error) => {
        console.error("Error fetching holdings:", error);
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
    <div style={{ width: "90vw", padding: "20px", margin: "0 auto" }}>
      <h2 style={{ textAlign: "center" }}>Current Holdings</h2>
      <table border="1" style={{ width: "100%", borderCollapse: "collapse", textAlign: "center" }}>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Quantity</th>
            <th>Day Change ($)</th>
            <th>Total Change ($)</th>
            <th>Market Value ($)</th>
            <th>Unit Cost ($)</th>
            <th>Total Cost ($)</th>
          </tr>
        </thead>
        <tbody>
          {holdings.length > 0 ? (
            holdings.map((holding, index) => (
              <tr key={index}>
                <td>{holding.ticker}</td>
                <td>{holding.quantity}</td>
                <td style={{ color: holding.day_change >= 0 ? "green" : "red" }}>
                  ${holding.day_change.toFixed(2)}
                </td>
                <td style={{ color: holding.total_change >= 0 ? "green" : "red" }}>
                  ${holding.total_change.toFixed(2)}
                </td>
                <td>${holding.market_value.toFixed(2)}</td>
                <td>${holding.unit_cost.toFixed(2)}</td>
                <td>${holding.total_cost.toFixed(2)}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="7">No holdings available.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default HoldingsTable;
