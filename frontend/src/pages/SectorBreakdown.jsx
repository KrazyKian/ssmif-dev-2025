import React, { useEffect, useState } from "react";
import axios from "axios";
import { AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from "recharts";

const API_BASE_URL = "http://localhost:8000";

const SectorBreakdown = () => {
  const [sectorData, setSectorData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/sector_breakdown`)
      .then((response) => {
        console.log("Raw API Data:", response.data);
        
        const formattedData = response.data.map(entry => {
          const dateFormatted = new Date(entry.date).toISOString().split("T")[0]; // Ensure correct date format
          
          // Convert proportions (0.3 → 30%)
          const sectorsAsPercentages = Object.fromEntries(
            Object.entries(entry.sectors).map(([sector, value]) => [sector, value * 100]) // Multiply by 100
          );

          return { date: dateFormatted, ...sectorsAsPercentages };
        });

        console.log("Formatted Data:", formattedData);
        setSectorData(formattedData);
      })
      .catch((error) => {
        console.error("Error fetching sector data:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <h2>Loading sector data. This may take a few seconds...</h2>;
  }

  // Get sector names dynamically
  const sectors = Object.keys(sectorData[0]).filter(key => key !== "date");

  return (
    <div style={{ width: "90vw", height: "80vh", padding: "20px", margin: "0 auto" }}>
      <h2 style={{ textAlign: "center" }}>Portfolio Sector Breakdown Over Time</h2>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={sectorData} margin={{ top: 40, right: 50, left: 50, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            angle={-30} 
            textAnchor="end" 
            tickFormatter={(date) => new Date(date).toLocaleDateString()} 
          />
          <YAxis 
            domain={[0, 100]}
            tickFormatter={(value) => `${value.toFixed(0)}%`} 
          />
          <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
          <Legend verticalAlign="top" align="center" height={30} />

          {sectors.map((sector, index) => (
            <Area 
              key={sector} 
              type="monotone" 
              dataKey={sector} 
              stackId="1" 
              stroke={`hsl(${index * 45}, 70%, 50%)`} 
              fill={`hsl(${index * 45}, 70%, 70%)`} 
              strokeWidth={2} 
            />
          ))}

        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SectorBreakdown;
