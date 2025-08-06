import React from 'react';

const Header: React.FC = () => {
  return (
    <div className="header">
      <h1 className="title">
        <span className="icon">🎯</span>
        Talent Match
      </h1>
      <p className="subtitle">
        AI-Powered Candidate Recommendation Engine
      </p>
    </div>
  );
};

export default Header; 