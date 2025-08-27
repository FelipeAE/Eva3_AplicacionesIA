import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="mb-3">
      <div className="d-flex justify-content-start mb-2">
        <div className="bg-white border rounded p-3" style={{ maxWidth: '70%' }}>
          <div className="fw-medium mb-2 text-success">
            IA está escribiendo...
          </div>
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;