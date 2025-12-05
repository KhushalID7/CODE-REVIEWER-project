import React, { useState } from 'react';
import MonacoEditor from '@monaco-editor/react';
import { FindingsPanel } from './components/FindingsPanel';
import { DiffViewer } from './components/DiffViewer';
import './styles/main.css';

const DEFAULT_CODE = `# Paste your Python code here\nprint('Hello, AI Reviewer!')`;

export default function App() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [findings, setFindings] = useState([]);
  const [diff, setDiff] = useState('');
  const [loading, setLoading] = useState(false);

  // Placeholder handlers
  const handleAnalyze = async () => {
    setLoading(true);
    // TODO: Call backend API to analyze code
    setTimeout(() => {
      setFindings([
        { line: 1, type: 'warning', message: 'Example warning: Unused variable', rule: 'W0612' },
      ]);
      setLoading(false);
    }, 1000);
  };

  const handleAutoFix = async () => {
    setLoading(true);
    // TODO: Call backend API to generate fix
    setTimeout(() => {
      setDiff(`--- a/main.py\n+++ b/main.py\n@@ -1,2 +1,2 @@\n-print('Hello, AI Reviewer!')\n+print('Hello, AI Code Reviewer!')`);
      setLoading(false);
    }, 1000);
  };

  const handleApplyPatch = () => {
    // TODO: Apply patch to code
    setCode(code.replace('Reviewer!', 'Code Reviewer!'));
    setDiff('');
  };

  return (
    <div className="app-container">
      <h1 className="title">AI Code Reviewer + Fixer</h1>
      <div className="editor-section">
        <MonacoEditor
          height="350px"
          language="python"
          value={code}
          onChange={setCode}
          theme="vs-dark"
        />
        <div className="button-group">
          <button onClick={handleAnalyze} disabled={loading}>Analyze</button>
          <button onClick={handleAutoFix} disabled={loading}>Auto-Fix</button>
          <button onClick={handleApplyPatch} disabled={!diff || loading}>Apply Patch</button>
        </div>
      </div>
      <FindingsPanel findings={findings} />
      <DiffViewer diff={diff} />
      <div className="download-section">
        <button onClick={() => navigator.clipboard.writeText(code)}>Copy Code</button>
        <a
          href={`data:text/plain;charset=utf-8,${encodeURIComponent(code)}`}
          download="main.py"
        >
          <button>Download Code</button>
        </a>
      </div>
    </div>
  );
}
