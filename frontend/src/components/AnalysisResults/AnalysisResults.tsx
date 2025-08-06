import React from 'react';
import type { Candidate } from '../../shared/types/index';

interface AnalysisResultsProps {
  results: Candidate[];
  isProcessing: boolean;
  progress: number;
  candidates: Candidate[];
  selectedCandidate: Candidate | null;
  onCandidateClick: (candidate: Candidate) => void;
}

const AnalysisResults: React.FC<AnalysisResultsProps> = ({
  results,
  isProcessing,
  progress,
  candidates,
  selectedCandidate,
  onCandidateClick
}) => {
  return (
    <div className="grid-item results-section">
      <div className="card">
        <h2 className="card-title">
          <span className="icon">🏆</span>
          Analysis Results
        </h2>

        {/* Processing Progress */}
        {isProcessing && (
          <div className="processing-container">
            <div className="progress-container">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="progress-text">
                Analyzing {candidates.length} candidates against job requirements...
              </p>
            </div>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && !isProcessing && (
          <div className="results-list">
            {results.map((candidate, index) => (
              <div
                key={candidate.id}
                className={`result-item ${selectedCandidate?.id === candidate.id ? 'selected' : ''}`}
                onClick={() => onCandidateClick(candidate)}
              >
                <div className="result-header">
                  <div className="result-rank">
                    <span className="rank-number">{index + 1}</span>
                  </div>
                  <div className="result-info">
                    <h3 className="result-name">{candidate.name}</h3>
                  </div>
                  <div className="result-score">
                    <div className="score-value">
                      {Math.round((candidate.similarityScore || 0) * 100)}%
                    </div>
                    <div className="score-label">Match Score</div>
                  </div>
                </div>

                {candidate.aiSummary && (
                  <div className="ai-summary">
                    <p className="summary-text">
                      <strong>AI Analysis:</strong> {candidate.aiSummary}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isProcessing && results.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🎯</div>
            <p className="empty-text">
              Add a job description and candidate resumes, then click "Find Best Matches" to get started.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisResults; 