import React from 'react';

interface InvitationCodeProps {
    value: string;
    onChange: (value: string) => void;
}

const InvitationCode: React.FC<InvitationCodeProps> = ({ value, onChange }) => {
    return (
        <div className="grid-item job-description-section">
            <div className="card">
                <h2 className="card-title">
                    <span className="icon">🔒</span>
                    Invitation Code
                </h2>
                <p className="card-description">
                    Enter the invitation code to access the matching service
                </p>
                <label className="input-label" htmlFor="invitation-code">Invitation Code</label>
                <input
                    id="invitation-code"
                    type="text"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder="Enter invitation code"
                    className="resume-input"
                />
            </div>
        </div>
    );
};

export default InvitationCode;


