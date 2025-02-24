import React, { useEffect, useState } from "react";
import axios from "axios";

const API_BASE_URL = "http://localhost:8000"; // Backend URL

const TradesTable = () => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/trades`)
      .then((response) => {
        setTrades(response.data.trades);
      })
      .catch((error) => {
        console.error("Error fetching trades:", error);
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
      <h2 style={{ textAlign: "center" }}>Trade History</h2>
      <table border="1" style={{ width: "100%", borderCollapse: "collapse", textAlign: "center" }}>
        <thead>
          <tr>
            <th>Date</th>
            <th>Ticker</th>
            <th>Quantity</th>
            <th>Unit Price ($)</th>
            <th>Total Price ($)</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>
          {trades.length > 0 ? (
            trades.map((trade, index) => (
              <tr key={index}>
                <td>{trade.Date}</td>
                <td>{trade.Ticker}</td>
                <td>{trade.Quantity}</td>
                <td>${trade.UnitPrice.toFixed(2)}</td>
                <td>${trade.TotalPrice.toFixed(2)}</td>
                <td 
                  style={{
                    fontWeight: "bold",
                    color: trade.Type.toUpperCase() === "BUY" ? "green" : "red",
                  }}
                >
                  {trade.Type}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="6">No trades found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default TradesTable;
