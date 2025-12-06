import React from 'react';

export function DiffViewer({ diff }) {
  if (!diff) return null;

  return (
    <div className="diff-viewer">
      <h2>🔧 Proposed Fix</h2>
      <pre className="diff-content">{diff}</pre>
      <p className="diff-hint">👆 Review the fix above, then click "Apply Fix" to update your code</p>
    </div>
  );
}
