"""Serve the Reference First browser prototype locally using only Python's standard library."""

import argparse
import copy
import json
import mimetypes
import threading
import uuid
import webbrowser
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from engine import Session


WEB_ROOT = Path(__file__).resolve().parent / "web"
COOKIE_NAME = "reference_first_session"
MAX_BODY_BYTES = 8192


class BrowserSession:
    def __init__(self):
        self.state = Session()
        self.lock = threading.RLock()


class PrototypeServer(ThreadingHTTPServer):
    """Loopback-only server; separate browser cookies receive separate engine states."""

    daemon_threads = True

    def __init__(self, port=8765, web_root=None):
        self.web_root = Path(web_root or WEB_ROOT).resolve()
        self.sessions = {}
        self.sessions_lock = threading.Lock()
        super().__init__(("127.0.0.1", port), PrototypeHandler)


class PrototypeHandler(BaseHTTPRequestHandler):
    server_version = "ReferenceFirst"
    sys_version = ""

    def log_message(self, format, *args):
        # The launcher prints the address; routine asset requests need no console noise.
        pass

    def _respond(self, status, content, content_type, head_only=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        cookie = getattr(self, "new_session_cookie", None)
        if cookie:
            self.send_header(
                "Set-Cookie",
                f"{COOKIE_NAME}={cookie}; Path=/; HttpOnly; SameSite=Strict",
            )
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

    def _json(self, status, payload, head_only=False):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._respond(status, data, "application/json; charset=utf-8", head_only)

    def _error(self, status, message, head_only=False):
        self._json(status, {"error": message}, head_only)

    def _check_host(self):
        port = self.server.server_address[1]
        host = self.headers.get("Host", "")
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if port == 80:
            allowed.update({"127.0.0.1", "localhost"})
        if host not in allowed:
            self._error(403, "Open the prototype using its local 127.0.0.1 or localhost address.")
            return False
        return True

    def _session(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except CookieError:
            cookies = SimpleCookie()
        morsel = cookies.get(COOKIE_NAME)
        session_id = morsel.value if morsel else None
        with self.server.sessions_lock:
            if session_id not in self.server.sessions:
                session_id = uuid.uuid4().hex
                self.server.sessions[session_id] = BrowserSession()
                self.new_session_cookie = session_id
            return self.server.sessions[session_id]

    @staticmethod
    def _snapshot(state):
        return copy.deepcopy({
            "case_id": state.case_id,
            "cases": [
                {"id": case_id, "title": case["title"], "question": case["question"]}
                for case_id, case in state.cases.items()
            ],
            "case": state.case,
            "decisions": state.decisions,
            "reviewed": state.reviewed,
            "ready": state.ready,
            "stopped": state.stopped,
            "result": state.result,
            "search_query": state.search_query,
            "available_reference_count": state.available_reference_count,
            "question_submitted": state.question_submitted,
            "requested_question": state.requested_question,
            "retrieval_message": state.retrieval_message,
            "can_undo_exclusion": state.can_undo_exclusion,
            "last_excluded_source_id": state.last_excluded_source_id,
        })

    def do_HEAD(self):
        self._get(head_only=True)

    def do_GET(self):
        self._get()

    def _get(self, head_only=False):
        if not self._check_host():
            return
        try:
            path = unquote(urlsplit(self.path).path)
        except ValueError:
            self._error(400, "The request URL is invalid.", head_only)
            return
        if path == "/api/session":
            session = self._session()
            with session.lock:
                snapshot = self._snapshot(session.state)
            self._json(200, snapshot, head_only)
            return
        if path.startswith("/api/"):
            self._error(404, "That API endpoint does not exist.", head_only)
            return
        try:
            relative = "index.html" if path == "/" else path.lstrip("/")
            if "\x00" in relative or "\\" in relative:
                raise ValueError("Invalid asset path")
            asset = (self.server.web_root / relative).resolve()
            asset.relative_to(self.server.web_root)
            if not asset.is_file():
                self._error(404, "That prototype file does not exist.", head_only)
                return
            data = asset.read_bytes()
        except (OSError, ValueError):
            self._error(404, "That prototype file does not exist.", head_only)
            return
        content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"
        self._respond(200, data, content_type, head_only)

    def _body(self):
        if self.headers.get("Transfer-Encoding"):
            raise ValueError("Chunked request bodies are not supported.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Content-Length must be a whole number.") from None
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError(f"Request body must be no larger than {MAX_BODY_BYTES} bytes.")
        if length == 0:
            return {}
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("Send the request as application/json.")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("The request body must contain valid JSON.") from None
        if not isinstance(data, dict):
            raise ValueError("The JSON request body must be an object.")
        return data

    def do_POST(self):
        if not self._check_host():
            return
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{self.headers.get('Host')}":
            self._error(403, "Requests must come from this prototype's local browser page.")
            return
        try:
            path = urlsplit(self.path).path
        except ValueError:
            self._error(400, "The request URL is invalid.")
            return
        fields = {
            "/api/decision": {"source_id", "choice"},
            "/api/generate": set(),
            "/api/case": {"case_id"},
            "/api/restart": set(),
            "/api/stop": set(),
            "/api/references": {"query"},
            "/api/question": {"question"},
            "/api/new-question": set(),
            "/api/undo-exclusion": set(),
        }
        if path not in fields:
            self._error(404, "That API endpoint does not exist.")
            return
        try:
            data = self._body()
            expected = fields[path]
            if set(data) != expected or any(not isinstance(data[key], str) for key in expected):
                names = ", ".join(sorted(expected)) or "no fields"
                raise ValueError(f"This action requires {names}; field values must be text.")
            session = self._session()
            with session.lock:
                state = session.state
                if path == "/api/decision":
                    state.decide(data["source_id"], data["choice"])
                elif path == "/api/generate":
                    state.generate()
                elif path == "/api/case":
                    state.change_case(data["case_id"])
                elif path == "/api/restart":
                    state.restart()
                elif path == "/api/stop":
                    state.stop()
                elif path == "/api/references":
                    state.add_references(data["query"])
                elif path == "/api/question":
                    state.ask_question(data["question"])
                elif path == "/api/new-question":
                    state.change_case("diary")
                elif path == "/api/undo-exclusion":
                    state.undo_last_exclusion()
                snapshot = self._snapshot(state)
        except ValueError as error:
            self._error(400, str(error))
            return
        except Exception:
            self._error(500, "The prototype could not complete that action. Restart the local server and try again.")
            return
        self._json(200, snapshot)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765, help="Local port (default: 8765).")
    parser.add_argument("--no-browser", action="store_true", help="Serve without opening a browser tab.")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535.")
    if not (WEB_ROOT / "index.html").is_file():
        parser.error("The browser files are missing. Keep the web folder beside this script.")
    try:
        server = PrototypeServer(port=args.port)
    except OSError as error:
        parser.error(f"Could not open the local server: {error}. Try a different --port.")
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"Reference First prototype: {url}", flush=True)
    print("Fictional evidence and simulated summaries. Press Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
