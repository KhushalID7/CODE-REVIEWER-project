import React from 'react';

export function DiffViewer({ diff }) {
  if (!diff) return null;
  return (
    <div className="diff-viewer">
      <h2>Unified Diff Preview</h2>
      <pre>{diff}</pre>
    </div>
  );
}
