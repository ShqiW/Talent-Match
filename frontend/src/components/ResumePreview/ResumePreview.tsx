import React from 'react';
import type { Candidate } from '../../shared/types/index';

interface ResumePreviewProps {
  selectedCandidate: Candidate | null;
}

const ResumePreview: React.FC<ResumePreviewProps> = ({ selectedCandidate }) => {
  return (
    <div className="grid-item preview-section">
      <div className="card">
        <h2 className="card-title">
          <span className="icon">📄</span>
          Resume Preview
        </h2>

        {selectedCandidate ? (
          <div className="preview-content">
            <div className="preview-header">
              <h3 className="preview-name">{selectedCandidate.name}</h3>
              <div className="preview-actions">
                {selectedCandidate.similarityScore && (
                  <div className="preview-score">
                    Match: {Math.round((selectedCandidate.similarityScore || 0) * 100)}%
                  </div>
                )}
              </div>
            </div>
            {/* <div>{selectedCandidate.aiSummary}</div> */}
            <div className="preview-text">
              {selectedCandidate.resume ? (
                <embed
                  title="Resume PDF Preview"
                  src={`data:application/pdf;base64,${selectedCandidate.resume}`}
                  width="100%"
                  height="600px"
                  style={{ border: 'none' }}
                />
              ) : (
                <p>{selectedCandidate.info}</p>
              )}
            </div>
          </div>
        ) : (
          <div className="preview-empty">
            <div className="preview-empty-icon">📄</div>
            <p className="preview-empty-text">
              Click on a candidate from the analysis results to preview their resume
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumePreview; 