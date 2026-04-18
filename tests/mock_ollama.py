#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("MOCK_OLLAMA_HOST", "127.0.0.1")
PORT = int(os.environ.get("MOCK_OLLAMA_PORT", "19114"))
MODELS = [{"name": "qwen2.5-coder:latest"}, {"name": "tiny-debug:1b"}]


class Handler(BaseHTTPRequestHandler):
    server_version = "MockOllama/0.1"

    def log_message(self, fmt: str, *args):
        return

    def _json(self, code: int, payload: dict):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/tags":
            self._json(200, {"models": MODELS})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return
        if self.path != "/api/chat":
            self._json(404, {"error": "not found"})
            return
        model = payload.get("model", "")
        installed = {m["name"] for m in MODELS}
        if model not in installed:
            self._json(404, {"error": f"model '{model}' not found"})
            return
        messages = payload.get("messages", [])
        user_message = ""
        for item in reversed(messages):
            if item.get("role") == "user":
                user_message = item.get("content", "")
                break
        response_text = (
            f"MODEL={model}\n"
            f"AUTO_CONTEXT={'yes' if '[CONTEXTO DE PROJETO]' in user_message else 'no'}\n"
            f"EXPLICIT_CONTEXT={'yes' if '[CONTEXTO EXPLICITO]' in user_message else 'no'}\n"
            f"PROMPT_LEN={len(user_message)}\n"
            f"PROMPT_HEAD={user_message[:120].replace(chr(10), ' ')}"
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        if payload.get("think"):
            chunk = {"message": {"role": "assistant", "thinking": "planejando..."}, "done": False}
            self.wfile.write((json.dumps(chunk) + "\n").encode("utf-8"))
            self.wfile.flush()
            time.sleep(0.01)
        mid = max(1, len(response_text) // 2)
        for idx, part in enumerate([response_text[:mid], response_text[mid:]]):
            chunk = {"message": {"role": "assistant", "content": part}, "done": idx == 1}
            self.wfile.write((json.dumps(chunk) + "\n").encode("utf-8"))
            self.wfile.flush()
            time.sleep(0.01)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"mock ollama listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
