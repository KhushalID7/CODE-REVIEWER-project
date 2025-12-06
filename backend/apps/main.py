"""FastAPI entrypoint for AI Code Reviewer backend."""

import os
import tempfile
from dotenv import load_dotenv

# Load .env FIRST, before any imports from local modules
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from . import schemas
from . import analyser
from . import linter_runner
from . import patch_utils
from . import llm_client

app = FastAPI(title="AI Code Reviewer")

# Add permissive CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Basic health check that includes LLM connectivity."""
    hc = llm_client.health_check(job_id="health")
    return {"status": "ok", "llm": hc}


@app.post("/api/analyze", response_model=schemas.AnalyzeResponse)
def analyze(payload: schemas.AnalyzeRequest):
    """Analyze code files for issues."""
    with tempfile.TemporaryDirectory() as td:
        for f in payload.files:
            target = os.path.join(td, f.path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(f.content)

        results = analyser.analyze_files(td)

    return schemas.AnalyzeResponse(findings=results)


@app.post("/api/generate_fix", response_model=schemas.GenerateFixResponse)
def generate_fix(payload: schemas.GenerateFixRequest):
    """Generate a fix for a code issue using LLM."""
    try:
        res = llm_client.generate_fix(
            payload.path, 
            payload.code, 
            payload.issue or {}, 
            job_id="generate_fix"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return schemas.GenerateFixResponse(
        success=res.get("success", False),
        patched_code=res.get("patched_code"),
        explanation=res.get("explanation"),
        meta=res.get("meta"),
    )


@app.post("/api/apply_patch", response_model=schemas.ApplyPatchResponse)
def apply_patch(payload: schemas.ApplyPatchRequest):
    """Apply a unified diff patch to files."""
    updated_files = []
    for f in payload.files:
        try:
            new_content = patch_utils.apply_patch_to_content(f.content, payload.patch)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Patch apply failed: {e}")
        updated_files.append(schemas.FileItem(path=f.path, content=new_content))

    return schemas.ApplyPatchResponse(files=updated_files)

