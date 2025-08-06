import React from 'react';
import type { Candidate } from '../../shared/types/index';

interface ResumeUploadProps {
  candidates: Candidate[];
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onTextInput: (text: string) => void;
  onRemoveCandidate: (id: string) => void;
  onAnalyze: () => void;
  onClearAll: () => void;
  isProcessing: boolean;
  jobDescription: string;
}

const ResumeUpload: React.FC<ResumeUploadProps> = ({
  candidates,
  onFileUpload,
  onTextInput,
  onRemoveCandidate,
  onAnalyze,
  onClearAll,
  isProcessing,
  jobDescription
}) => {
  return (
    <div className="grid-item upload-section">
      <div className="card">
        <h2 className="card-title">
          <span className="icon">👥</span>
          Upload Resume
        </h2>
        <p className="card-description">
          Upload PDF files or paste text manually
        </p>

        {/* File Upload */}
        <div className="file-upload-area">
          <div className="upload-icon">📁</div>
          <p className="upload-text">
            Drop PDF files here or click to browse
          </p>
          <p className="upload-note">
            Upload resume files (PDF only)
          </p>
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={onFileUpload}
            className="file-input"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="upload-button">
            Choose PDF Files
          </label>
        </div>

        {/* Manual Text Input */}
        <div className="manual-input">
          <label className="input-label">
            Or paste candidate resume text directly:
          </label>
          <textarea
            placeholder="Paste candidate resume text here..."
            className="resume-input"
            onBlur={(e) => {
              if (e.target.value.trim()) {
                onTextInput(e.target.value);
                e.target.value = '';
              }
            }}
          />
        </div>

        {/* Candidate List */}
        {candidates.length > 0 && (
          <div className="candidate-list">
            <h4 className="list-title">Added Candidates:</h4>
            {candidates.map((candidate) => (
              <div key={candidate.id} className="candidate-item">
                <div className="candidate-info">
                  <span className="file-icon">📄</span>
                  <span className="candidate-name">{candidate.name}</span>
                </div>
                <div className="candidate-actions">
                  <button
                    onClick={() => onRemoveCandidate(candidate.id)}
                    className="remove-button"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="action-buttons">
          <button
            onClick={onAnalyze}
            disabled={isProcessing || !jobDescription.trim() || candidates.length === 0}
            className="analyze-button"
          >
            {isProcessing ? (
              <>
                <span className="loading-spinner"></span>
                Processing...
              </>
            ) : (
              <>
                <span className="icon">✨</span>
                Find Best Matches
              </>
            )}
          </button>
          <button onClick={onClearAll} className="clear-button">
            Clear All
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResumeUpload; 