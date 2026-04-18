#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "tests" / "mock_ollama.py"


def run(cmd, *, cwd=None, env=None, input_text=None, check=True):
    proc = subprocess.run(cmd, cwd=cwd, env=env, input=input_text, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(str(x) for x in cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    return proc


def wait_for_server(env):
    for _ in range(50):
        proc = run([sys.executable, str(ROOT / "kaos-cli"), "--models"], env=env, check=False)
        if proc.returncode == 0:
            return
        time.sleep(0.1)
    raise RuntimeError("mock ollama did not start in time")


def main() -> int:
    run([sys.executable, "-m", "py_compile", str(ROOT / "kaos-cli")])
    run(["bash", "-n", str(ROOT / "install.sh")])
    run(["bash", "-n", str(ROOT / "uninstall.sh")])

    temp_home = Path(tempfile.mkdtemp(prefix="kaos-home-"))
    temp_project = Path(tempfile.mkdtemp(prefix="kaos-project-"))
    server_env = os.environ.copy()
    server_env["MOCK_OLLAMA_PORT"] = "19114"
    server = subprocess.Popen([sys.executable, str(MOCK)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=server_env)

    base_env = os.environ.copy()
    base_env["HOME"] = str(temp_home)
    base_env["OLLAMA_HOST"] = "http://127.0.0.1:19114"
    base_env["KAOS_MODEL"] = "modelo-inexistente"
    base_env["KAOS_PROVIDER"] = "ollama"
    if "GOOGLE_API_KEY" in base_env:
        del base_env["GOOGLE_API_KEY"]
    base_env["PATH"] = f"{temp_home / '.local' / 'bin'}:{base_env['PATH']}"

    try:
        wait_for_server(base_env)
        run(["bash", str(ROOT / "install.sh")], env=base_env)
        wrapper = temp_home / ".local" / "bin" / "kaos-cli"
        if not wrapper.exists():
            raise RuntimeError("wrapper nao foi instalado")
        (temp_project / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (temp_project / "README.md").write_text("# Demo\nProjeto de teste\n", encoding="utf-8")

        proc1 = run([str(wrapper), "analise", "este", "projeto"], cwd=temp_project, env=base_env)
        assert "MODEL=qwen2.5-coder:latest" in proc1.stdout, proc1.stdout
        assert "AUTO_CONTEXT=yes" in proc1.stdout, proc1.stdout
        assert "Contexto ativado..." in proc1.stderr, proc1.stderr
        assert "nao encontrado" in proc1.stderr.lower(), proc1.stderr

        huge_prompt = "A" * 12000
        proc2 = run([str(wrapper), "--stdin"], cwd=temp_project, env=base_env, input_text=huge_prompt)
        assert "PROMPT_LEN=12000" in proc2.stdout or "PROMPT_LEN=12001" in proc2.stdout, proc2.stdout

        proc3 = run([str(wrapper), "--read", "main.py", "explique", "este", "arquivo"], cwd=temp_project, env=base_env)
        assert "EXPLICIT_CONTEXT=yes" in proc3.stdout, proc3.stdout

        proc4 = run([str(wrapper), "--doctor"], env=base_env)
        assert "Status" in proc4.stdout and "OK" in proc4.stdout, proc4.stdout

        proc5 = run([str(wrapper), "--models"], env=base_env)
        assert "qwen2.5-coder:latest" in proc5.stdout, proc5.stdout

        print("[OK] Todos os testes passaram.")
        return 0
    finally:
        server.send_signal(signal.SIGTERM)
        try:
            server.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server.kill()
        shutil.rmtree(temp_home, ignore_errors=True)
        shutil.rmtree(temp_project, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
