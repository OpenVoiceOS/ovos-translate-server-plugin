"""A 4xx from a reachable server surfaces as that error, not as "servers down"."""
import json
import unittest
from unittest.mock import patch

import requests

from ovos_translate_server_plugin import OVOSLangDetectServer, OVOSTranslateServer


def _reply(status: int, body: str, content_type: str) -> requests.Response:
    r = requests.Response()
    r.status_code = status
    r._content = body.encode()
    r.headers["Content-Type"] = content_type
    return r


BAD_TARGET = _reply(400, json.dumps({"error": "ValueError",
                                     "detail": "Invalid target language: zz"}),
                    "application/json")
DETECT_PT = _reply(200, "pt", "text/plain; charset=utf-8")
SERVERS = ["https://srv1", "https://srv2"]


class TestClientErrors(unittest.TestCase):

    @patch("requests.get")
    def test_translate_400_raises_the_server_error(self, mock_get):
        mock_get.return_value = BAD_TARGET
        tx = OVOSTranslateServer(config={"host": SERVERS})
        with self.assertRaises(ValueError) as ctx:
            tx.translate("hello", "zz", "en")
        self.assertEqual(str(ctx.exception), "400: Invalid target language: zz")

    @patch("requests.get")
    def test_translate_400_does_not_try_the_next_server(self, mock_get):
        mock_get.return_value = BAD_TARGET
        tx = OVOSTranslateServer(config={"host": SERVERS})
        with self.assertRaises(ValueError):
            tx.translate("hello", "zz", "en")
        self.assertEqual(mock_get.call_count, 1)

    @patch("requests.get")
    def test_translate_with_detected_source_400_raises_the_server_error(self, mock_get):
        mock_get.side_effect = [DETECT_PT, BAD_TARGET]
        tx = OVOSTranslateServer(config={"host": SERVERS})
        with self.assertRaises(ValueError) as ctx:
            tx.translate("hello", "zz")
        self.assertEqual(str(ctx.exception), "400: Invalid target language: zz")
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_detect_400_raises_the_server_error(self, mock_get):
        mock_get.return_value = _reply(400, json.dumps({"error": "ValueError",
                                                        "detail": "bad text"}),
                                       "application/json")
        dt = OVOSLangDetectServer(config={"host": SERVERS})
        with self.assertRaises(ValueError) as ctx:
            dt.detect("hello")
        self.assertEqual(str(ctx.exception), "400: bad text")
        self.assertEqual(mock_get.call_count, 1)

    @patch("requests.get")
    def test_detect_probs_400_raises_the_server_error(self, mock_get):
        mock_get.return_value = _reply(400, "no good", "text/plain")
        dt = OVOSLangDetectServer(config={"host": SERVERS})
        with self.assertRaises(ValueError) as ctx:
            dt.detect_probs("hello")
        self.assertEqual(str(ctx.exception), "400: no good")

    @patch("requests.get")
    def test_5xx_still_fails_over_after_the_change(self, mock_get):
        mock_get.side_effect = [_reply(503, "{}", "application/json"),
                                _reply(200, "Hallo", "text/plain")]
        tx = OVOSTranslateServer(config={"host": SERVERS})
        self.assertEqual(tx.translate("hello", "de", "en"), "Hallo")
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_all_servers_down_still_raises_runtime_error(self, mock_get):
        mock_get.return_value = _reply(503, "{}", "application/json")
        tx = OVOSTranslateServer(config={"host": SERVERS})
        with self.assertRaisesRegex(RuntimeError, "All OVOS Translate servers are down"):
            tx.translate("hello", "de", "en")

    @patch("requests.get")
    def test_404_fails_over_to_the_next_server(self, mock_get):
        mock_get.side_effect = [_reply(404, "", "text/plain"),
                                _reply(200, "Hallo", "text/plain")]
        tx = OVOSTranslateServer(config={"host": SERVERS})
        self.assertEqual(tx.translate("hello", "de", "en"), "Hallo")
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_detect_404_fails_over_to_the_next_server(self, mock_get):
        mock_get.side_effect = [_reply(404, "{}", "application/json"), DETECT_PT]
        dt = OVOSLangDetectServer(config={"host": SERVERS})
        self.assertEqual(dt.detect("hello"), "pt")

    @patch("requests.get")
    def test_failed_detect_reply_is_not_used_as_the_source_language(self, mock_get):
        not_found = _reply(404, '{"detail":"Not Found"}', "application/json")
        mock_get.side_effect = [not_found, DETECT_PT,
                                _reply(200, "Hallo", "text/plain")]
        tx = OVOSTranslateServer(config={"host": SERVERS})
        self.assertEqual(tx.translate("hello", "de"), "Hallo")
        urls = [c.args[0] for c in mock_get.call_args_list]
        self.assertEqual(urls, ["https://srv1/detect/hello",
                                "https://srv2/detect/hello",
                                "https://srv2/translate/pt/de/hello"])

    @patch("requests.get")
    def test_422_detail_list_is_readable(self, mock_get):
        body = json.dumps({"detail": [{"loc": ["path", "tgt_lang"],
                                       "msg": "field required",
                                       "type": "missing"}]})
        mock_get.return_value = _reply(422, body, "application/json")
        tx = OVOSTranslateServer(config={"host": SERVERS})
        with self.assertRaises(ValueError) as ctx:
            tx.translate("hello", "de", "en")
        self.assertEqual(str(ctx.exception), "422: path.tgt_lang: field required")
        self.assertEqual(mock_get.call_count, 1)
