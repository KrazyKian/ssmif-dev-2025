import React from "react";
import SharpeRatioChart from "../components/SharpeRatioChart";

const SharpeRatio = () => {
  return (
    <div>
      <h1 style={{ textAlign: "center" }}>Portfolio Sharpe Ratio</h1>
      <SharpeRatioChart />
    </div>
  );
};

export default SharpeRatio;
