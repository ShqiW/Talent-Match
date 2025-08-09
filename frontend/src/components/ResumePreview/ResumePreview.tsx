// import { useState, useEffect } from 'react';
import React from 'react';
import type { Candidate } from '../../shared/types/index';

interface ResumePreviewProps {
  selectedCandidate: Candidate | null;
}

// const PDFViewer: React.FC<{ selectedCandidate: Candidate }> = ({ selectedCandidate }) => {
//   const [pdfUrl, setPdfUrl] = useState<string | null>(null);

//   useEffect(() => {
//     if (selectedCandidate.resume) {
//       const binaryString = atob(selectedCandidate.resume);
//       const bytes = new Uint8Array(binaryString.length);
//       for (let i = 0; i < binaryString.length; i++) {
//         bytes[i] = binaryString.charCodeAt(i);
//       }
//       const blob = new Blob([bytes], { type: 'application/pdf' });
//       const url = URL.createObjectURL(blob);
//       setPdfUrl(url);

//       return () => {
//         URL.revokeObjectURL(url);
//       };
//     } else {
//       setPdfUrl(null);
//     }
//   }, [selectedCandidate.resume]);

//   if (!pdfUrl) {
//     return <div>Loading PDF...</div>;
//   }

//   return (
//     <embed
//       title="Resume PDF Preview"
//       src={pdfUrl}
//       width="100%"
//       height="600px"
//       style={{ border: 'none' }}
//     />
//   );
// };
const ResumePreview: React.FC<ResumePreviewProps> = ({ selectedCandidate }) => {
  // console.log(selectedCandidate)
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
                // <PDFViewer selectedCandidate={selectedCandidate} />
                <iframe
                  title="Resume PDF Preview"
                  src={`/static/pdf/${selectedCandidate.resume_name}`}
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