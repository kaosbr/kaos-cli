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

def test_build_project_context_empty(tmp_path):
    # Invalid directory
    context = kaos_cli.build_project_context(str(tmp_path / "does_not_exist"))
    assert context == ""

def test_build_project_context_structure(tmp_path):
    # Create structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "README.md").write_text("Test Project")

    context = kaos_cli.build_project_context(str(tmp_path))

    assert f"Project structure of {tmp_path.name}:" in context
    assert "src/" in context
    assert "main.py" in context
    assert "README.md" in context

    assert "--- FILE: README.md ---" in context
    assert "Test Project" in context

    assert "--- FILE: src/main.py ---" in context
    assert "print('hello')" in context

def test_build_project_context_ignores(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("git config")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "test.js").write_text("js")

    (tmp_path / "valid.py").write_text("valid")

    context = kaos_cli.build_project_context(str(tmp_path))

    assert "valid.py" in context
    assert "--- FILE: valid.py ---" in context

    assert ".git/" not in context
    assert "node_modules/" not in context
    assert "config" not in context
    assert "test.js" not in context

def test_build_project_context_gitignore(tmp_path):
    (tmp_path / ".gitignore").write_text("ignored_dir/\nignored_file.txt\n# comment")

    (tmp_path / "ignored_dir").mkdir()
    (tmp_path / "ignored_dir" / "file.py").write_text("ignored")

    (tmp_path / "ignored_file.txt").write_text("text")
    (tmp_path / "test.py").write_text("python")

    context = kaos_cli.build_project_context(str(tmp_path))

    assert "test.py" in context
    assert "--- FILE: test.py ---" in context

    assert "ignored_dir/" not in context

    # We must explicitly check that `ignored_file.txt` is not included in the '--- FILE' outputs
    # In the current implementation, `if f in ignore_patterns` does exact matching for files,
    # so simple filenames will be ignored in the directory list.
    # (Wildcards like `*.txt` are only matched via fnmatch for DIRECTORIES in the first pass,
    # but not via fnmatch for individual files in the tree view, although they are ignored in the file content dump).
    assert "--- FILE: ignored_file.txt ---" not in context
    assert "ignored_file.txt" not in context.split("--- FILE")[0] # Check directory tree output
