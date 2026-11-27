import json
import unittest
from unittest.mock import patch

import requests

from ovos_translate_server_plugin import OVOSLangDetectServer, OVOSTranslateServer


def _response(body: str, content_type: str) -> requests.Response:
    r = requests.Response()
    r.status_code = 200
    r._content = body.encode("utf-8")
    r.headers["Content-Type"] = content_type
    r.encoding = "utf-8"
    return r


def fastapi(value) -> requests.Response:
    """A reply as ovos-translate-server 0.1.0 and later sends it."""
    return _response(json.dumps(value), "application/json")


def flask(text: str) -> requests.Response:
    """A reply as the Flask server (0.0.x) sends it."""
    return _response(text, "text/html; charset=utf-8")


class TestFastAPIServerReplies(unittest.TestCase):
    @patch("requests.get")
    def test_detect_returns_the_whole_code(self, mock_get):
        mock_get.return_value = fastapi("pt")
        dt = OVOSLangDetectServer(config={"host": "http://srv"})
        self.assertEqual(dt.detect("olá mundo"), "pt")

    @patch("requests.get")
    def test_translate_uses_the_detected_code_in_the_url(self, mock_get):
        mock_get.side_effect = [fastapi("pt"), fastapi("hello world")]
        tx = OVOSTranslateServer(config={"host": "http://srv"})
        self.assertEqual(tx.translate("olá mundo", target="en"), "hello world")
        self.assertEqual(mock_get.call_args_list[1].args[0],
                         "http://srv/translate/pt/en/olá mundo")

    @patch("requests.get")
    def test_translation_has_no_json_quotes(self, mock_get):
        mock_get.return_value = fastapi('she said "hi"')
        tx = OVOSTranslateServer(config={"host": "http://srv", "skip_detection": True})
        self.assertEqual(tx.translate("ela disse \"olá\"", target="en"), 'she said "hi"')


class TestFlaskServerReplies(unittest.TestCase):
    @patch("requests.get")
    def test_detect_plain_text(self, mock_get):
        mock_get.return_value = flask("pt")
        dt = OVOSLangDetectServer(config={"host": "http://srv"})
        self.assertEqual(dt.detect("olá mundo"), "pt")

    @patch("requests.get")
    def test_translate_plain_text(self, mock_get):
        mock_get.side_effect = [flask("pt"), flask("hello world")]
        tx = OVOSTranslateServer(config={"host": "http://srv"})
        self.assertEqual(tx.translate("olá mundo", target="en"), "hello world")
        self.assertEqual(mock_get.call_args_list[1].args[0],
                         "http://srv/translate/pt/en/olá mundo")

    @patch("requests.get")
    def test_numeric_translation_stays_text(self, mock_get):
        mock_get.return_value = flask("42")
        tx = OVOSTranslateServer(config={"host": "http://srv", "skip_detection": True})
        self.assertEqual(tx.translate("quarenta e dois", target="en"), "42")

    @patch("requests.get")
    def test_quoted_translation_keeps_its_quotes(self, mock_get):
        mock_get.return_value = flask('"good morning"')
        tx = OVOSTranslateServer(config={"host": "http://srv", "skip_detection": True})
        self.assertEqual(tx.translate('"bom dia"', target="en"), '"good morning"')

    @patch("requests.get")
    def test_bracketed_translation_stays_whole(self, mock_get):
        mock_get.return_value = flask('["good morning"]')
        tx = OVOSTranslateServer(config={"host": "http://srv", "skip_detection": True})
        self.assertEqual(tx.translate('["bom dia"]', target="en"), '["good morning"]')


if __name__ == "__main__":
    unittest.main()
