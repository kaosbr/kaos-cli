import unittest
import tempfile
import os
import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]

import importlib.machinery

# Dynamically import the cli script as a module
cli_path = ROOT / "kaos-cli"
loader = importlib.machinery.SourceFileLoader("kaos_cli", str(cli_path))
spec = importlib.util.spec_from_loader("kaos_cli", loader)
kaos_cli = importlib.util.module_from_spec(spec)
sys.modules["kaos_cli"] = kaos_cli
loader.exec_module(kaos_cli)

class TestKaosCliCore(unittest.TestCase):
    def test_build_project_context_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some dummy files
            (temp_path / "main.py").write_text("print('hello')", encoding="utf-8")
            (temp_path / "README.md").write_text("# Test Project", encoding="utf-8")

            # Create an ignored directory and file
            (temp_path / "node_modules").mkdir()
            (temp_path / "node_modules" / "ignore_me.js").write_text("console.log('no')", encoding="utf-8")

            # Create .gitignore
            (temp_path / ".gitignore").write_text("test.log\n/build/\n", encoding="utf-8")
            (temp_path / "test.log").write_text("log data", encoding="utf-8")

            (temp_path / "build").mkdir()
            (temp_path / "build" / "output.bin").write_text("binary", encoding="utf-8")

            context = kaos_cli.build_project_context(temp_dir)

            self.assertIn("main.py", context)
            self.assertIn("print('hello')", context)
            self.assertIn("README.md", context)
            self.assertIn("# Test Project", context)

            # Should ignore these
            self.assertNotIn("ignore_me.js", context)

            self.assertNotIn("test.log", context)
            self.assertNotIn("output.bin", context)

    def test_build_project_context_not_a_dir(self):
        with tempfile.NamedTemporaryFile() as f:
            context = kaos_cli.build_project_context(f.name)
            self.assertEqual(context, "")

    @patch('urllib.request.urlopen')
    def test_ollama_client_check_models_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"models": [{"name": "qwen2.5-coder"}, {"name": "llama3"}]}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = kaos_cli.OllamaClient("http://localhost:11434")
        models = client.check_models()

        self.assertEqual(models, ["qwen2.5-coder", "llama3"])

    @patch('urllib.request.urlopen')
    def test_ollama_client_check_models_failure(self, mock_urlopen):
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Mocked URL Error")

        client = kaos_cli.OllamaClient("http://localhost:11434")
        models = client.check_models()

        self.assertEqual(models, [])

    @patch.object(kaos_cli.OllamaClient, 'check_models')
    def test_ollama_client_resolve_model_found(self, mock_check_models):
        mock_check_models.return_value = ["qwen2.5-coder", "llama3"]
        client = kaos_cli.OllamaClient("http://localhost:11434")

        resolved = client.resolve_model("llama3")
        self.assertEqual(resolved, "llama3")

    @patch.object(kaos_cli.OllamaClient, 'check_models')
    @patch('sys.stderr', new_callable=MagicMock)
    def test_ollama_client_resolve_model_not_found(self, mock_stderr, mock_check_models):
        mock_check_models.return_value = ["qwen2.5-coder", "llama3"]
        client = kaos_cli.OllamaClient("http://localhost:11434")

        resolved = client.resolve_model("unknown_model")
        # Should fallback to the first model in the list
        self.assertEqual(resolved, "qwen2.5-coder")

    @patch.object(kaos_cli.OllamaClient, 'check_models')
    def test_ollama_client_resolve_model_no_models(self, mock_check_models):
        mock_check_models.return_value = []
        client = kaos_cli.OllamaClient("http://localhost:11434")

        resolved = client.resolve_model("unknown_model")
        # Should fallback to the requested model if no models available to fallback to
        self.assertEqual(resolved, "unknown_model")

    def test_gemini_client_resolve_model(self):
        client = kaos_cli.GeminiClient("fake_key")

        # Gemini always resolves to requested right now
        resolved = client.resolve_model("gemini-1.5-pro")
        self.assertEqual(resolved, "gemini-1.5-pro")

    @patch.dict(os.environ, {}, clear=True)
    @patch('kaos_cli.Path.home')
    @patch('kaos_cli.Path.cwd')
    def test_load_config_defaults(self, mock_cwd, mock_home):
        mock_home.return_value = Path("/nonexistent/home")
        mock_cwd.return_value = Path("/nonexistent/cwd")

        config = kaos_cli.load_config()
        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.key, "")
        self.assertEqual(config.host, "http://127.0.0.1:11434")
        self.assertEqual(config.model, "qwen2.5-coder:latest")
        self.assertEqual(config.system, "Você é o KAOS CLI, especialista sênior em engenharia.")
        self.assertEqual(config.auto_context, True)

    @patch.dict(os.environ, {}, clear=True)
    @patch('kaos_cli.Path.home')
    @patch('kaos_cli.Path.cwd')
    def test_load_config_env_vars_precedence(self, mock_cwd, mock_home):
        mock_home.return_value = Path("/nonexistent/home")
        mock_cwd.return_value = Path("/nonexistent/cwd")

        env_vars = {
            "KAOS_PROVIDER": "gemini",
            "GOOGLE_API_KEY": "test_key",
            "OLLAMA_HOST": "http://other:11434",
            "KAOS_MODEL": "gemini-1.5-pro",
            "KAOS_SYSTEM_PROMPT": "New Prompt",
            "KAOS_AUTO_CONTEXT": "0"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = kaos_cli.load_config()
            self.assertEqual(config.provider, "gemini")
            self.assertEqual(config.key, "test_key")
            self.assertEqual(config.host, "http://other:11434")
            self.assertEqual(config.model, "gemini-1.5-pro")
            self.assertEqual(config.system, "New Prompt")
            self.assertEqual(config.auto_context, False)

    @patch.dict(os.environ, {}, clear=True)
    @patch('kaos_cli.Path.home')
    @patch('kaos_cli.Path.cwd')
    def test_load_config_file_cwd_precedence(self, mock_cwd, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir) / "home"
            cwd_dir = Path(temp_dir) / "cwd"

            home_config_dir = home_dir / ".config/kaos-cli"
            home_config_dir.mkdir(parents=True)
            home_config = home_config_dir / "config.env"
            home_config.write_text("KAOS_PROVIDER=ollama\nKAOS_MODEL=qwen-home\n")

            cwd_dir.mkdir(parents=True)
            cwd_config = cwd_dir / "config.env"
            cwd_config.write_text("KAOS_PROVIDER=gemini\nKAOS_MODEL=gemini-cwd\nGOOGLE_API_KEY=test_key\n")

            mock_home.return_value = home_dir
            mock_cwd.return_value = cwd_dir

            config = kaos_cli.load_config()
            self.assertEqual(config.provider, "gemini") # Overridden by cwd
            self.assertEqual(config.model, "gemini-cwd") # Overridden by cwd

    @patch.dict(os.environ, {}, clear=True)
    @patch('kaos_cli.Path.home')
    @patch('kaos_cli.Path.cwd')
    def test_load_config_file_parsing_edge_cases(self, mock_cwd, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd_dir = Path(temp_dir)
            cwd_config = cwd_dir / "config.env"
            cwd_config.write_text(
                "# This is a comment\n"
                "MALFORMED LINE\n"
                "KAOS_PROVIDER=gemini  \n"
                "GOOGLE_API_KEY=test_key\n"
                "KAOS_MODEL='gemini-1.5-pro'\n"
                "KAOS_SYSTEM_PROMPT=\"Quote Prompt\"\n"
            )

            mock_home.return_value = Path("/nonexistent/home")
            mock_cwd.return_value = cwd_dir

            config = kaos_cli.load_config()
            self.assertEqual(config.provider, "gemini") # Trims trailing space
            self.assertEqual(config.model, "gemini-1.5-pro") # Strips quotes
            self.assertEqual(config.system, "Quote Prompt") # Strips quotes

    @patch.dict(os.environ, {}, clear=True)
    @patch('kaos_cli.Path.home')
    @patch('kaos_cli.Path.cwd')
    def test_load_config_gemini_fallback(self, mock_cwd, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd_dir = Path(temp_dir)
            cwd_config = cwd_dir / "config.env"
            cwd_config.write_text("KAOS_PROVIDER=gemini\nKAOS_MODEL=gemini-cwd\n")

            mock_home.return_value = Path("/nonexistent/home")
            mock_cwd.return_value = cwd_dir

            config = kaos_cli.load_config()
            # Missing API key should force fallback to ollama
            self.assertEqual(config.provider, "ollama")

if __name__ == '__main__':
    unittest.main()
