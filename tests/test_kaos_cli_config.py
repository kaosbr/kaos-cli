import importlib.machinery
import importlib.util
import os
from pathlib import Path

import pytest

# Dynamically load kaos-cli
root_dir = Path(__file__).parent.parent
kaos_cli_path = root_dir / "kaos-cli"

loader = importlib.machinery.SourceFileLoader("kaos_cli", str(kaos_cli_path))
spec = importlib.util.spec_from_loader("kaos_cli", loader)
kaos_cli = importlib.util.module_from_spec(spec)
loader.exec_module(kaos_cli)

@pytest.fixture(autouse=True)
def clean_env():
    # Store original env
    original_env = os.environ.copy()

    # Remove config vars for clean tests
    keys_to_remove = ["KAOS_PROVIDER", "GOOGLE_API_KEY", "OLLAMA_HOST", "KAOS_MODEL", "KAOS_SYSTEM_PROMPT", "KAOS_AUTO_CONTEXT"]
    for key in keys_to_remove:
        if key in os.environ:
            del os.environ[key]

    # Mock Path.cwd and Path.home to not load user/local config.env files
    # We will do this by temporarily overriding Path.home and Path.cwd locally in the test if needed.

    yield

    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)

def test_load_config_defaults(monkeypatch, tmp_path):
    # Mock paths to empty directories so it doesn't find real config.env
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    config = kaos_cli.load_config()

    assert config.provider == "ollama"
    assert config.key == ""
    assert config.host == "http://127.0.0.1:11434"
    assert config.model == "qwen2.5-coder:latest"
    assert config.system == "Você é o KAOS CLI, especialista sênior em engenharia."
    assert config.auto_context is True

def test_load_config_env_vars(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    os.environ["KAOS_PROVIDER"] = "gemini"
    os.environ["GOOGLE_API_KEY"] = "test_key"
    os.environ["OLLAMA_HOST"] = "http://test:1111"
    os.environ["KAOS_MODEL"] = "test-model"
    os.environ["KAOS_SYSTEM_PROMPT"] = "Test prompt"
    os.environ["KAOS_AUTO_CONTEXT"] = "0"

    config = kaos_cli.load_config()

    assert config.provider == "gemini"
    assert config.key == "test_key"
    assert config.host == "http://test:1111"
    assert config.model == "test-model"
    assert config.system == "Test prompt"
    assert config.auto_context is False

def test_load_config_gemini_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # If provider is gemini but no key is provided, it falls back to ollama
    os.environ["KAOS_PROVIDER"] = "gemini"

    config = kaos_cli.load_config()
    assert config.provider == "ollama"

def test_load_config_file(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    config_file = tmp_path / "config.env"
    config_file.write_text("KAOS_MODEL=file-model\nOLLAMA_HOST='http://file:2222'")

    config = kaos_cli.load_config()

    assert config.model == "file-model"
    assert config.host == "http://file:2222"
