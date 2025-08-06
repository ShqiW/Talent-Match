import React from 'react';

interface JobDescriptionProps {
  jobDescription: string;
  onJobDescriptionChange: (value: string) => void;
}

const JobDescription: React.FC<JobDescriptionProps> = ({
  jobDescription,
  onJobDescriptionChange
}) => {
  return (
    <div className="grid-item job-description-section">
      <div className="card">
        <h2 className="card-title">
          <span className="icon">📋</span>
          Job Description
        </h2>
        <p className="card-description">
          Enter the job description to find the best candidates
        </p>
        <textarea
          value={jobDescription}
          onChange={(e) => onJobDescriptionChange(e.target.value)}
          placeholder="Enter the job description here..."
          className="job-description-input"
        />
      </div>
    </div>
  );
};

export default JobDescription; 