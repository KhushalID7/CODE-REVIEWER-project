import React from 'react';

export function FindingsPanel({ findings }) {
  if (!findings || findings.length === 0) {
    return (
      <div className="findings-panel">
        <h2>📋 Analysis Results</h2>
        <p className="no-findings">Click "Analyze" to check your code for issues</p>
      </div>
    );
  }

  // Success message
  if (findings[0]?.type === 'info') {
    return (
      <div className="findings-panel">
        <h2>📋 Analysis Results</h2>
        <div className="finding-item success">
          <span className="finding-message">{findings[0].message}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="findings-panel">
      <h2>📋 Analysis Results ({findings.length} issue{findings.length > 1 ? 's' : ''})</h2>
      <div className="findings-list">
        {findings.map((finding, idx) => (
          <div key={idx} className={`finding-item ${finding.type}`}>
            <span className="finding-line">Line {finding.line}</span>
            <span className="finding-type">{finding.type.toUpperCase()}</span>
            <span className="finding-message">{finding.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
