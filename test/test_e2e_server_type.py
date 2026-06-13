# pylint: disable=missing-docstring,redefined-outer-name,protected-access
"""End-to-end tests for the server_type adapter over a real socket.

The plugin *is* the client, so these run the real plugin (real ``requests``
HTTP) against a real local server speaking the vendor wire format. No mocking,
no external network.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ovos_translate_server_plugin import OVOSTranslateServer


class _VendorHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        path = self.path.split("?")[0]
        if path.endswith("/translate") and not path.endswith("/v2/translate"):  # LibreTranslate
            self._json({"translatedText": "hola mundo"})
        elif path.endswith("/v2/translate"):  # DeepL
            self._json({"translations": [{"text": "Hallo Welt"}]})
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture(scope="module")
def vendor_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _VendorHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_libretranslate_end_to_end(vendor_server):
    tx = OVOSTranslateServer(config={"server_type": "libretranslate", "host": vendor_server})
    assert tx.translate("hello world", target="es", source="en") == "hola mundo"


def test_deepl_end_to_end(vendor_server):
    tx = OVOSTranslateServer(config={"server_type": "deepl", "host": vendor_server,
                                     "api_key": "dl-test"})
    assert tx.translate("hello world", target="de", source="en") == "Hallo Welt"
