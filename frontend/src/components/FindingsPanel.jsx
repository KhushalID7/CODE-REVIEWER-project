import React from 'react';

export function FindingsPanel({ findings }) {
  if (!findings.length) return null;
  return (
    <div className="findings-panel">
      <h2>Findings</h2>
      <ul>
        {findings.map((f, idx) => (
          <li key={idx} className={f.type}>
            <strong>Line {f.line}:</strong> {f.type.toUpperCase()} - {f.message} <em>({f.rule})</em>
          </li>
        ))}
      </ul>
    </div>
  );
}
