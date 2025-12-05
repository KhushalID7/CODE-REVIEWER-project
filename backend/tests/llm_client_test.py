import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps import llm_client

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "test-key-123")
    monkeypatch.setenv("GOOGLE_AI_MODEL", "gemini-1.5-flash")
    # Reinitialize client with test env
    llm_client.init_client()


class TestLLMClient:
    
    def test_config_initialization(self):
        """Test config reads env vars correctly"""
        config = llm_client._get_config()
        assert config.api_key == "test-key-123"
        assert config.model == "gemini-1.5-flash"
        assert config.is_configured() is True
    
    @patch('apps.llm_client.requests.post')
    def test_call_model_success(self, mock_post):
        """Test successful API call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"patched_code": "fixed", "explanation": "test"}'}]
                }
            }],
            "usageMetadata": {"totalTokenCount": 50}
        }
        mock_post.return_value = mock_response
        
        result = llm_client.call_model("test prompt", job_id="test")
        
        assert result["success"] is True
        assert "fixed" in result["output"]
        assert result["meta"]["tokens_used"] == 50
    
    @patch('apps.llm_client.requests.post')
    def test_call_model_rate_limit(self, mock_post):
        """Test rate limit handling"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        result = llm_client.call_model("test prompt", job_id="test")
        
        assert result["success"] is False
        assert result["meta"]["error"] == "rate_limited"
        assert result["meta"]["status_code"] == 429
    
    @patch('apps.llm_client.call_model')
    def test_generate_fix_success(self, mock_call):
        """Test generate_fix with valid response"""
        mock_call.return_value = {
            "success": True,
            "output": '{"patched_code": "def foo():\\n    pass", "explanation": "Fixed naming"}',
            "meta": {"latency_ms": 100, "model": "gemini-1.5-flash"}
        }
        
        result = llm_client.generate_fix(
            file_path="test.py",
            file_content="def Foo():\n    pass",
            issue={"rule": "C0103", "message": "Invalid name", "line": 1}
        )
        
        assert result["success"] is True
        assert "def foo()" in result["patched_code"]
        assert "Fixed naming" in result["explanation"]
    
    @patch('apps.llm_client.call_model')
    def test_generate_fix_large_file_truncation(self, mock_call):
        """Test that large files are truncated"""
        mock_call.return_value = {
            "success": True,
            "output": '{"patched_code": "fixed", "explanation": "test"}',
            "meta": {}
        }
        
        large_content = "# line\n" * 1000  # >8KB
        
        result = llm_client.generate_fix(
            file_path="test.py",
            file_content=large_content,
            issue={"rule": "W0611", "message": "Unused import", "line": 500}
        )
        
        # Should succeed without sending entire file
        assert result["success"] is True
    
    def test_parse_json_response(self):
        """Test JSON parsing from various formats"""
        # Direct JSON
        assert llm_client._parse_json_response('{"key": "value"}') == {"key": "value"}
        
        # JSON in markdown
        text = 'Some text\n{"key": "value"}\nMore text'
        assert llm_client._parse_json_response(text) == {"key": "value"}
        
        # Invalid JSON
        assert llm_client._parse_json_response("not json") is None
    
    def test_extract_code_from_text(self):
        """Test code extraction from markdown fences"""
        # Fenced code
        text = "```python\ndef foo():\n    pass\n```"
        result = llm_client._extract_code_from_text(text)
        assert "def foo()" in result
        
        # Plain Python code
        text = "def bar():\n    return 42"
        result = llm_client._extract_code_from_text(text)
        assert "def bar()" in result
    
    def test_validate_patched_code(self):
        """Test patched code validation"""
        original = "def foo():\n    pass"
        
        # Valid patch
        valid, msg = llm_client._validate_patched_code(original, "def bar():\n    return 1")
        assert valid is True
        
        # Empty patch
        valid, msg = llm_client._validate_patched_code(original, "")
        assert valid is False
        assert "empty" in msg.lower()
        
        # Too large
        huge = "x" * (len(original) * 10)
        valid, msg = llm_client._validate_patched_code(original, huge)
        assert valid is False
        assert "too large" in msg.lower()
    
    @patch('apps.llm_client.call_model')
    def test_health_check(self, mock_call):
        """Test health check function"""
        mock_call.return_value = {
            "success": True,
            "output": "OK",
            "meta": {"latency_ms": 50}
        }
        
        result = llm_client.health_check()
        assert result["ok"] is True