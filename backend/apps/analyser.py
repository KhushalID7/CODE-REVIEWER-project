"""Analyze files and provide beginner-friendly explanations."""
import os
from typing import List
from . import linter_runner
from . import llm_client


def analyze_files(workspace_path: str) -> List[dict]:
    """Walk the workspace and run linters on supported files.
    Returns a beginner-friendly list of findings.
    """
    findings = []
    
    for root, dirs, files in os.walk(workspace_path):
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                
                # Run pylint
                issues = linter_runner.run_pylint(fpath)
                
                # Filter out noise (conventions that don't matter for beginners)
                ignored_rules = [
                    "missing-final-newline",
                    "missing-module-docstring",
                    "missing-class-docstring",
                    "missing-function-docstring",
                    "invalid-name",
                    "line-too-long",
                    "trailing-whitespace",
                ]
                
                for issue in issues:
                    rule = issue.get("message-id", "")
                    msg_type = issue.get("type", "")
                    
                    # Skip conventions and refactor suggestions
                    if msg_type in ["convention", "refactor"]:
                        continue
                    
                    # Skip ignored rules
                    if rule in ignored_rules:
                        continue
                    
                    # Only keep actual errors and warnings
                    findings.append({
                        "file": os.path.relpath(fpath, workspace_path),
                        "line": issue.get("line", 0),
                        "type": msg_type,
                        "message": issue.get("message", ""),
                        "rule": rule,
                        "tool": "pylint"  # ADD THIS FIELD
                    })
    
    # If no real issues found
    if len(findings) == 0:
        return [
            {
                "file": "analysis",
                "line": 0,
                "type": "info",
                "message": "✅ Your code looks good! No critical errors found.",
                "rule": "success",
                "tool": "AI Reviewer"  # ADD THIS FIELD
            }
        ]
    
    return findings

