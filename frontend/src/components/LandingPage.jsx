import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./LandingPage.css";

const LandingPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleButtonClick = () => {
    if (user) {
      navigate("/dashboard");
    } else {
      navigate("/login");
    }
  };

  return (
    <div className="landing-container">
      <div className="content-wrapper">
        <div className="hero-section">
          <h1>
            The New Standard For
            <span className="gradient-text"> Cold Outreach</span>
          </h1>
          <p className="hero-description">
            Save countless hours in your job search and increase your success rate with ColdDigger,
            the all-in-one platform designed specifically for automated job applications.
          </p>
          <button className="cta-button" onClick={handleButtonClick}>
            {user ? "Go to Dashboard" : "Get Started →"}
          </button>
        </div>
        
        <div className="illustration-section">
          {/* You can add an illustration or 3D model here */}
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
