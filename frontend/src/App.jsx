import React, { useState } from "react";
import MonacoEditor from "@monaco-editor/react";
import { FindingsPanel } from "./components/FindingsPanel";
import { DiffViewer } from "./components/DiffViewer";
import { analyzeCode, generateFix, applyPatch } from "./api/client";
import "./styles/main.css";

const DEFAULT_CODE = `# Paste your Python code here
print('Hello, AI Reviewer!')`;

export default function App() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [findings, setFindings] = useState([]);
  const [patchedCode, setPatchedCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleAnalyze = async () => {
    setLoading(true);
    setMessage('🔍 Analyzing your code...');
    setPatchedCode('');
    
    try {
      const response = await analyzeCode([
        { path: "main.py", content: code }
      ]);
      
      const issues = response.data.findings || [];
      setFindings(issues);
      
      if (issues.length === 0 || issues[0]?.type === 'info') {
        setMessage('✅ No issues found! Your code looks great.');
      } else {
        setMessage(`Found ${issues.length} issue(s) that need attention.`);
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.response?.data?.detail || error.message}`);
      setFindings([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoFix = async () => {
    if (findings.length === 0 || findings[0]?.type === 'info') {
      setMessage('✅ Nothing to fix!');
      return;
    }

    setLoading(true);
    setMessage('🤖 AI is generating a fix...');
    
    try {
      // Get the first actual error/warning
      const firstIssue = findings[0];
      
      const response = await generateFix("main.py", code, {
        rule: firstIssue.rule,
        message: firstIssue.message,
        line: firstIssue.line
      });
      
      if (response.data.success && response.data.patched_code) {
        setPatchedCode(response.data.patched_code);
        setMessage(`💡 ${response.data.explanation || 'Fix generated successfully!'}`);
      } else {
        setMessage('❌ Could not generate fix. Try manual correction.');
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPatch = async () => {
    if (!patchedCode) {
      setMessage('⚠️ No fix available to apply');
      return;
    }

    setLoading(true);
    setMessage('✨ Applying fix...');
    
    try {
      // Simply replace the code with the patched version
      setCode(patchedCode);
      setPatchedCode('');
      setFindings([]);
      setMessage('✅ Fix applied! Run Analyze again to verify.');
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1 className="title">🤖 AI Code Reviewer</h1>

      <div className="editor-section">
        <MonacoEditor
          height="400px"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={(value) => setCode(value || '')}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
          }}
        />
        <div className="button-group">
          <button onClick={handleAnalyze} disabled={loading}>
            {loading ? "⏳ Analyzing..." : "🔍 Analyze"}
          </button>
          <button 
            onClick={handleAutoFix} 
            disabled={loading || findings.length === 0 || findings[0]?.type === 'info'}
          >
            {loading ? "⏳ Generating..." : "🤖 Generate Fix"}
          </button>
          <button onClick={handleApplyPatch} disabled={loading || !patchedCode}>
            {loading ? "⏳ Applying..." : "✨ Apply Fix"}
          </button>
        </div>
        {message && <p className="message">{message}</p>}
      </div>

      <FindingsPanel findings={findings} />
      {patchedCode && <DiffViewer diff={patchedCode} />}
    </div>
  );
}
