"""
llm_client.py — Google AI Studio integration for code fixing and analysis.

Exposes pure functions to generate fixes, polish patches, and summarize code snippets.
Handles retries, validation, and returns predictable JSON responses.
"""

import os
import json
import logging
import time
from typing import Optional, Dict, Any
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration & Initialization
# ============================================================================

class LLMClientConfig:
    """Configuration container for LLM client."""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_AI_API_KEY")
        # Use full model name with 'models/' prefix
        self.model = os.getenv("GOOGLE_AI_MODEL", "models/gemini-2.5-flash")
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.backoff_seconds = float(os.getenv("LLM_BACKOFF_SECONDS", "1.0"))
        # Keep v1beta endpoint
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent"
        
        if not self.api_key:
            logger.warning("GOOGLE_AI_API_KEY not set. LLM functions will fail.")
    
    def is_configured(self) -> bool:
        """Check if API key is present."""
        return bool(self.api_key)


# Global config instance
_config: Optional[LLMClientConfig] = None


def init_client() -> None:
    """Initialize the LLM client by reading environment variables."""
    global _config
    _config = LLMClientConfig()
    logger.info(f"LLM client initialized with model: {_config.model}")


def _get_config() -> LLMClientConfig:
    """Lazy-init and return config."""
    global _config
    if _config is None:
        init_client()
    return _config


# ============================================================================
# Prompt Templates
# ============================================================================

def _build_generate_fix_prompt(file_path: str, snippet: str, issue: dict) -> str:
    """
    Build a prompt for generate_fix that asks for complete corrected code.
    
    IMPORTANT: We ask for the ENTIRE corrected file content, not just the changed line.
    This is because the frontend will replace the entire editor content with the fix.
    """
    rule = issue.get("rule", "")
    message = issue.get("message", "")
    line_num = issue.get("line", 0)
    
    prompt = f"""You are a Python code fixer. Your task is to fix the following code issue.

**File:** {file_path}
**Issue on line {line_num}:** {message} (rule: {rule})

**Current Code:**
```python
{snippet}
```

**Instructions:**
1. Fix ONLY the specific issue mentioned above
2. Return the COMPLETE corrected code (all lines, not just the changed part)
3. Preserve ALL existing logic, comments, and formatting
4. Do NOT add new features or change unrelated code
5. Do NOT add extra comments explaining the fix

**Output Format:**
Return your response as JSON with this exact structure:
{{
    "patched_code": "... complete corrected code here ...",
    "explanation": "Brief explanation of what was fixed"
}}

The "patched_code" field must contain the ENTIRE file with the fix applied, preserving all original lines except the ones that needed fixing.
"""
    return prompt


def _build_polish_patch_prompt(original: str, candidate_patch: str) -> str:
    """Build prompt for polish_patch function."""
    prompt = f"""You are a code review assistant. Polish the following patch into clean unified diff format.

Original code:
{original}

Candidate patch (changes to make):
{candidate_patch}

Return ONLY valid JSON with key "patch_text" containing the unified diff.
Do not include any other text or markdown.

Example response:
{{"patch_text": "--- a/file.py\\n+++ b/file.py\\n@@ -1,3 +1,3 @@\\n..."}}

Now provide the polished diff:"""
    
    return prompt


def _build_summarize_prompt(snippet: str, style: str = "concise") -> str:
    """Build prompt for summarize_snippet function."""
    prompt = f"""You are a code summarizer. Provide a {style} summary of this code snippet.

Code:
{snippet}

Return ONLY valid JSON with key "summary" (1-2 sentences max).
Do not include any other text or markdown.

Example response:
{{"summary": "This function..."}}

Now summarize:"""
    
    return prompt


# ============================================================================
# Core API Call Function
# ============================================================================

def call_model(
    prompt: str,
    *,
    max_tokens: int = 512,
    temperature: float = 0.0,
    job_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Generic call to Google AI Studio (Gemini) text generation endpoint.
    
    Args:
        prompt: The input prompt
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0 = deterministic)
        job_id: Caller job ID for logging
    
    Returns:
        {
            "success": bool,
            "output": str or null,
            "meta": {
                "model": str,
                "latency_ms": float,
                "status_code": int,
                "error": str or null,
                "tokens_used": int or null
            }
        }
    """
    config = _get_config()
    
    if not config.is_configured():
        return {
            "success": False,
            "output": None,
            "meta": {
                "error": "API key not configured",
                "status_code": 0,
                "latency_ms": 0
            }
        }
    
    start_time = time.time()
    url = f"{config.endpoint}?key={config.api_key}"
    
    headers = {"Content-Type": "application/json"}
    # Updated payload format for Gemini API
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "candidateCount": 1
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
    }
    
    # Retry logic with exponential backoff
    last_error = None
    for attempt in range(config.max_retries):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=config.timeout_seconds
            )
            latency_ms = (time.time() - start_time) * 1000
            
            # Handle rate limiting with longer backoff
            if response.status_code == 429:
                if attempt < config.max_retries - 1:
                    wait_time = config.backoff_seconds * (2 ** attempt) + 5
                    logger.warning(f"Rate limited. Retry {attempt+1} in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                return {
                    "success": False,
                    "output": None,
                    "meta": {
                        "error": "rate_limited",
                        "status_code": 429,
                        "latency_ms": latency_ms,
                        "job_id": job_id
                    }
                }
            
            # Handle other 5xx errors (transient)
            if 500 <= response.status_code < 600 and attempt < config.max_retries - 1:
                wait_time = config.backoff_seconds * (2 ** attempt)
                logger.warning(f"Server error {response.status_code}. Retry {attempt+1} in {wait_time}s")
                time.sleep(wait_time)
                continue
            
            # Handle 4xx errors (fail fast)
            if 400 <= response.status_code < 500:
                error_text = response.text[:200]
                return {
                    "success": False,
                    "output": None,
                    "meta": {
                        "error": f"Client error: {error_text}",
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                        "job_id": job_id
                    }
                }
            
            # Success - Updated for Gemini response format
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Extract text from Gemini response structure
                    output = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    
                    # Get token usage if available
                    usage_metadata = data.get("usageMetadata", {})
                    tokens_used = usage_metadata.get("totalTokenCount")
                    
                    logger.info(f"[{job_id}] LLM call successful ({latency_ms:.0f}ms, {tokens_used or 0} tokens)")
                    return {
                        "success": True,
                        "output": output,
                        "meta": {
                            "model": config.model,
                            "latency_ms": latency_ms,
                            "status_code": 200,
                            "error": None,
                            "tokens_used": tokens_used,
                            "job_id": job_id
                        }
                    }
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    logger.error(f"Failed to parse response: {e}")
                    return {
                        "success": False,
                        "output": None,
                        "meta": {
                            "error": f"Response parse error: {str(e)[:100]}",
                            "status_code": 200,
                            "latency_ms": latency_ms,
                            "job_id": job_id
                        }
                    }
            
            # Unexpected status
            return {
                "success": False,
                "output": None,
                "meta": {
                    "error": f"Unexpected status {response.status_code}",
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "job_id": job_id
                }
            }
        
        except requests.Timeout:
            last_error = "timeout"
            if attempt < config.max_retries - 1:
                wait_time = config.backoff_seconds * (2 ** attempt)
                logger.warning(f"Timeout. Retry {attempt+1} in {wait_time}s")
                time.sleep(wait_time)
        except requests.RequestException as e:
            last_error = str(e)[:100]
            if attempt < config.max_retries - 1:
                wait_time = config.backoff_seconds * (2 ** attempt)
                logger.warning(f"Request error: {last_error}. Retry {attempt+1} in {wait_time}s")
                time.sleep(wait_time)
    
    latency_ms = (time.time() - start_time) * 1000
    logger.error(f"[{job_id}] LLM call failed after {config.max_retries} retries: {last_error}")
    return {
        "success": False,
        "output": None,
        "meta": {
            "error": last_error or "max_retries exceeded",
            "status_code": 0,
            "latency_ms": latency_ms,
            "job_id": job_id
        }
    }


# ============================================================================
# Output Parsing & Validation
# ============================================================================

def _parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """Try to extract and parse JSON from response text."""
    if not text:
        return None
    
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON within text (e.g., markdown fence)
    if "{" in text:
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        if start_idx < end_idx:
            try:
                return json.loads(text[start_idx:end_idx])
            except json.JSONDecodeError:
                pass
    
    return None


def _extract_code_from_text(text: str) -> Optional[str]:
    """Extract code from markdown fences or return text if it looks like code."""
    if not text:
        return None
    
    # Try to extract from markdown fence
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            # Usually: ```\ncode\n```
            return parts[1].strip()
    
    # If text looks like code (has indentation, keywords), return it
    if any(keyword in text for keyword in ["def ", "class ", "import ", "if ", "for "]):
        return text.strip()
    
    return None


def _validate_patched_code(original: str, patched: str) -> tuple[bool, str]:
    """
    Sanity check on patched code.
    Returns: (is_valid, error_message)
    """
    if not patched or not isinstance(patched, str):
        return False, "Patched code is empty or not a string"
    
    if len(patched) > len(original) * 5:
        return False, "Patched code too large (>5x original)"
    
    if len(patched) == 0:
        return False, "Patched code is empty"
    
    return True, ""





# ============================================================================
# Public API Functions
# ============================================================================

def generate_fix(
    file_path: str,
    file_content: str,
    issue: Dict[str, Any],
    job_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Generate a fix for a code issue using the LLM.
    
    Args:
        file_path: Path to the file
        file_content: Full content or snippet of the file
        issue: Dict with keys: rule, message, line, (optional) context
        job_id: Caller job ID for logging
    
    Returns:
        {
            "success": bool,
            "patched_code": str or null,
            "explanation": str or null,
            "meta": {
                "model": str,
                "latency_ms": float,
                "error": str or null
            }
        }
    """
    # Truncate file content if too large
    if len(file_content) > 8192:
        lines = file_content.split("\n")
        line_num = issue.get("line", 1)
        start = max(0, line_num - 20)
        end = min(len(lines), line_num + 20)
        file_content = "\n".join(lines[start:end])
        logger.info(f"[{job_id}] Truncated file content to {len(file_content)} chars")
    
    # Build prompt and call model
    prompt = _build_generate_fix_prompt(file_path, file_content, issue)
    llm_response = call_model(prompt, max_tokens=1024, temperature=0.0, job_id=job_id)
    
    if not llm_response["success"]:
        return {
            "success": False,
            "patched_code": None,
            "explanation": None,
            "meta": llm_response["meta"]
        }
    
    # Parse response
    output = llm_response["output"]
    parsed = _parse_json_response(output)
    
    if parsed:
        patched_code = parsed.get("patched_code")
        explanation = parsed.get("explanation", "")
    else:
        # Fallback: try to extract code
        patched_code = _extract_code_from_text(output)
        explanation = "Auto-extracted from model output"
        logger.warning(f"[{job_id}] Fallback parsing used for {file_path}")
    
    # Validate
    is_valid, error_msg = _validate_patched_code(file_content, patched_code or "")
    
    if not is_valid:
        logger.error(f"[{job_id}] Validation failed: {error_msg}")
        return {
            "success": False,
            "patched_code": None,
            "explanation": None,
            "meta": {
                **llm_response["meta"],
                "error": f"validation_failed: {error_msg}"
            }
        }
    
    logger.info(f"[{job_id}] generate_fix successful for {file_path}")
    return {
        "success": True,
        "patched_code": patched_code,
        "explanation": explanation,
        "meta": llm_response["meta"]
    }


def polish_patch(
    original: str,
    candidate_patch: str,
    job_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Polish a candidate patch into clean unified diff format.
    
    Args:
        original: Original code
        candidate_patch: The proposed changes
        job_id: Caller job ID for logging
    
    Returns:
        {
            "success": bool,
            "patch_text": str or null,
            "meta": { ... }
        }
    """
    prompt = _build_polish_patch_prompt(original, candidate_patch)
    llm_response = call_model(prompt, max_tokens=2048, temperature=0.0, job_id=job_id)
    
    if not llm_response["success"]:
        return {
            "success": False,
            "patch_text": None,
            "meta": llm_response["meta"]
        }
    
    output = llm_response["output"]
    parsed = _parse_json_response(output)
    
    if parsed and "patch_text" in parsed:
        patch_text = parsed["patch_text"]
    else:
        patch_text = output
        logger.warning(f"[{job_id}] Fallback parsing for polish_patch")
    
    logger.info(f"[{job_id}] polish_patch successful")
    return {
        "success": True,
        "patch_text": patch_text,
        "meta": llm_response["meta"]
    }


def summarize_snippet(
    snippet: str,
    *,
    style: str = "concise",
    job_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Generate a short summary of a code snippet.
    
    Args:
        snippet: Code snippet to summarize
        style: "concise" or "detailed"
        job_id: Caller job ID for logging
    
    Returns:
        {
            "success": bool,
            "summary": str or null,
            "meta": { ... }
        }
    """
    prompt = _build_summarize_prompt(snippet, style=style)
    llm_response = call_model(prompt, max_tokens=256, temperature=0.0, job_id=job_id)
    
    if not llm_response["success"]:
        return {
            "success": False,
            "summary": None,
            "meta": llm_response["meta"]
        }
    
    output = llm_response["output"]
    parsed = _parse_json_response(output)
    
    if parsed and "summary" in parsed:
        summary = parsed["summary"]
    else:
        summary = output
        logger.warning(f"[{job_id}] Fallback parsing for summarize_snippet")
    
    logger.info(f"[{job_id}] summarize_snippet successful")
    return {
        "success": True,
        "summary": summary,
        "meta": llm_response["meta"]
    }


def health_check(job_id: str = "health") -> Dict[str, Any]:
    """
    Quick health check to validate API credentials and connectivity.
    
    Returns:
        {
            "ok": bool,
            "meta": { ... }
        }
    """
    config = _get_config()
    
    if not config.is_configured():
        return {
            "ok": False,
            "meta": {"error": "API key not configured"}
        }
    
    prompt = "Say 'OK' only."
    response = call_model(prompt, max_tokens=10, temperature=0.0, job_id=job_id)
    
    return {
        "ok": response["success"],
        "meta": response["meta"]
    }
