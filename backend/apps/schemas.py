from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class FileItem(BaseModel):
    path: str
    content: str


class AnalyzeRequest(BaseModel):
    files: List[FileItem]


class Finding(BaseModel):
    file: str
    line: int
    type: str  # 'error', 'warning', 'info'
    message: str
    rule: str
    tool: Optional[str] = "pylint"  # Make it optional with default


class AnalyzeResponse(BaseModel):
    findings: List[Finding]


class GenerateFixRequest(BaseModel):
    path: str
    code: str
    issue: Optional[Dict[str, Any]] = None


class GenerateFixResponse(BaseModel):
    success: bool
    patched_code: Optional[str] = None
    explanation: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class ApplyPatchRequest(BaseModel):
    files: List[FileItem]
    patch: str


class ApplyPatchResponse(BaseModel):
    files: List[FileItem]
