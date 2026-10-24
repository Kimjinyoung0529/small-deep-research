import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from small_deep_research.llm import OpenAICompatLLM


def test_openai_compat_roundtrip():
    seen = {}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"] = self.path
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen["auth"] = self.headers.get("Authorization")
            out = json.dumps({"choices": [{"message": {"content": " 안녕 "}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    llm = OpenAICompatLLM(f"http://127.0.0.1:{srv.server_port}/v1", model="m", api_key="k")
    assert llm.chat([{"role": "user", "content": "hi"}], max_tokens=7) == "안녕"
    assert seen["path"] == "/v1/chat/completions" and seen["body"]["max_tokens"] == 7 and seen["auth"] == "Bearer k"
    srv.server_close()
