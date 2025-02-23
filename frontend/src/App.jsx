import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Trades from "./pages/Trades";
import PortfolioValue from "./pages/PortfolioValue"; // Import Portfolio Value Page
import PortfolioVsSP500 from "./pages/PortfolioVsSP500"; // Import Performance Page
import SectorBreakdown from "./pages/SectorBreakdown"; // Import Sector Breakdown Page
import Holdings from "./pages/Holdings"; // Import Holdings Page
import SharpeRatio from "./pages/SharpeRatio"; // Import Sharpe Ratio Page
import Navbar from "./components/NavBar";

function App() {
  return (
    <Router>
      <div>
        <Navbar></ Navbar>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/trades" element={<Trades />} />
          <Route path="/portfolio-value" element={<PortfolioValue />} />
          <Route path="/portfolio-vs-sp500" element={<PortfolioVsSP500 />} />
          <Route path="/sector-breakdown" element={<SectorBreakdown />} />
          <Route path="/holdings" element={<Holdings />} />
          <Route path="/sharpe-ratio" element={<SharpeRatio />} />

        </Routes>
      </div>
    </Router>
  );
}

export default App;
