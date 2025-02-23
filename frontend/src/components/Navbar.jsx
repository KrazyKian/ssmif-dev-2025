import React from "react";
import { NavLink } from "react-router-dom";
import "./Navbar.css"; // Import CSS for styling

const Navbar = () => {
  return (
    <nav className="navbar">
      <ul className="nav-list">
        <li><NavLink to="/" className="nav-link">Home</NavLink></li>
        <li><NavLink to="/trades" className="nav-link">Trades</NavLink></li>
        <li><NavLink to="/portfolio-value" className="nav-link">Portfolio Value</NavLink></li>
        <li><NavLink to="/portfolio-vs-sp500" className="nav-link">Portfolio vs S&P 500</NavLink></li>
        <li><NavLink to="/sector-breakdown" className="nav-link">Sector Breakdown</NavLink></li>
        <li><NavLink to="/holdings" className="nav-link">Current Holdings</NavLink></li>
        <li><NavLink to="/sharpe-ratio" className="nav-link">Sharpe Ratio</NavLink></li>
      </ul>
    </nav>
  );
};

export default Navbar;
