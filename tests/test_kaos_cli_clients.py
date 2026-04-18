import importlib.machinery
import importlib.util
import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Dynamically load kaos-cli
root_dir = Path(__file__).parent.parent
kaos_cli_path = root_dir / "kaos-cli"

loader = importlib.machinery.SourceFileLoader("kaos_cli", str(kaos_cli_path))
spec = importlib.util.spec_from_loader("kaos_cli", loader)
kaos_cli = importlib.util.module_from_spec(spec)
loader.exec_module(kaos_cli)

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self._data = json.dumps(json_data).encode("utf-8")

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def test_ollama_check_models(monkeypatch):
    client = kaos_cli.OllamaClient("http://localhost:11434")

    def mock_urlopen(req, timeout=None):
        return MockResponse({"models": [{"name": "qwen2.5-coder:latest"}, {"name": "llama3:latest"}]})

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    models = client.check_models()
    assert models == ["qwen2.5-coder:latest", "llama3:latest"]

def test_ollama_check_models_fail(monkeypatch):
    client = kaos_cli.OllamaClient("http://localhost:11434")

    def mock_urlopen(req, timeout=None):
        raise Exception("Connection Refused")

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    models = client.check_models()
    assert models == []

def test_ollama_resolve_model_exact_match(monkeypatch):
    client = kaos_cli.OllamaClient("http://localhost:11434")
    monkeypatch.setattr(client, "check_models", lambda: ["qwen2.5-coder:latest", "llama3:latest"])

    resolved = client.resolve_model("llama3:latest")
    assert resolved == "llama3:latest"

def test_ollama_resolve_model_fallback(monkeypatch):
    client = kaos_cli.OllamaClient("http://localhost:11434")
    monkeypatch.setattr(client, "check_models", lambda: ["qwen2.5-coder:latest", "llama3:8b"])

    resolved = client.resolve_model("llama3:latest")
    assert resolved == "llama3:8b"

def test_ollama_resolve_model_no_connection(monkeypatch):
    client = kaos_cli.OllamaClient("http://localhost:11434")
    monkeypatch.setattr(client, "check_models", lambda: [])

    resolved = client.resolve_model("llama3:latest")
    assert resolved == "llama3:latest"

def test_gemini_check_models():
    client = kaos_cli.GeminiClient("fake_key")
    models = client.check_models()
    assert "gemini-1.5-pro" in models

def test_gemini_resolve_model():
    client = kaos_cli.GeminiClient("fake_key")
    resolved = client.resolve_model("any-model")
    assert resolved == "any-model"
