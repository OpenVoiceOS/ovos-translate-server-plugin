"""Tests for configurable timeout and 5xx failover (issue #20)."""
import unittest
from unittest.mock import patch, Mock, call

import requests

from ovos_translate_server_plugin import OVOSTranslateServer, OVOSLangDetectServer

_DEFAULT_TIMEOUT = 20


class TestTimeoutConfig(unittest.TestCase):

    def test_default_timeout(self):
        dt = OVOSLangDetectServer()
        self.assertEqual(dt.timeout, _DEFAULT_TIMEOUT)

    def test_configurable_timeout(self):
        dt = OVOSLangDetectServer(config={"timeout": 5})
        self.assertEqual(dt.timeout, 5)

    def test_translate_default_timeout(self):
        tx = OVOSTranslateServer()
        self.assertEqual(tx.timeout, _DEFAULT_TIMEOUT)

    def test_translate_configurable_timeout(self):
        tx = OVOSTranslateServer(config={"timeout": 10})
        self.assertEqual(tx.timeout, 10)


class TestDetectTimeout(unittest.TestCase):

    @patch("requests.get")
    def test_detect_passes_timeout(self, mock_get):
        """timeout kwarg must be forwarded to requests.get"""
        mock_get.return_value = Mock(ok=True, status_code=200,
                                     json=Mock(return_value=["en"]),
                                     text="en")
        dt = OVOSLangDetectServer(config={"timeout": 7, "host": "https://srv1"})
        dt.detect("hello")
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs.get("timeout"), 7)

    @patch("requests.get")
    def test_detect_times_out_and_raises(self, mock_get):
        """All servers timing out must raise RuntimeError."""
        mock_get.side_effect = requests.exceptions.Timeout
        dt = OVOSLangDetectServer(config={"host": ["https://srv1", "https://srv2"]})
        with self.assertRaises(RuntimeError):
            dt.detect("hello")

    @patch("requests.get")
    def test_detect_5xx_fails_over(self, mock_get):
        """5xx from first server must try the next; success on second must be returned."""
        bad = Mock(ok=False, status_code=503)
        good = Mock(ok=True, status_code=200, json=Mock(return_value=["fr"]), text="fr")
        mock_get.side_effect = [bad, good]
        dt = OVOSLangDetectServer(config={"host": ["https://srv-bad", "https://srv-good"]})
        result = dt.detect("bonjour")
        self.assertEqual(result, "fr")
        self.assertEqual(mock_get.call_count, 2)


class TestDetectProbsTimeout(unittest.TestCase):

    @patch("requests.get")
    def test_detect_probs_5xx_failover(self, mock_get):
        """5xx on /classify must try the next server."""
        bad = Mock(ok=False, status_code=500)
        good = Mock(ok=True, status_code=200, json=Mock(return_value={"en": 0.9}))
        mock_get.side_effect = [bad, good]
        dt = OVOSLangDetectServer(config={"host": ["https://srv-bad", "https://srv-good"]})
        result = dt.detect_probs("hello")
        self.assertEqual(result, {"en": 0.9})

    @patch("requests.get")
    def test_detect_probs_timeout_failover(self, mock_get):
        """Timeout on first /classify server must try the next."""
        good = Mock(ok=True, status_code=200, json=Mock(return_value={"en": 0.8}))
        mock_get.side_effect = [requests.exceptions.Timeout, good]
        dt = OVOSLangDetectServer(config={"host": ["https://srv-slow", "https://srv-fast"]})
        result = dt.detect_probs("hello")
        self.assertEqual(result, {"en": 0.8})


class TestTranslateTimeout(unittest.TestCase):

    @patch("requests.get")
    def test_translate_passes_timeout(self, mock_get):
        mock_get.return_value = Mock(ok=True, status_code=200, text="Hola")
        tx = OVOSTranslateServer(config={"timeout": 12, "host": "https://srv1",
                                          "skip_detection": True})
        tx.translate("Hello", target="es", source="en")
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs.get("timeout"), 12)

    @patch("requests.get")
    def test_translate_5xx_failover(self, mock_get):
        """5xx on first translate server must try the next."""
        bad = Mock(ok=False, status_code=503)
        good = Mock(ok=True, status_code=200, text="Hola")
        mock_get.side_effect = [bad, good]
        tx = OVOSTranslateServer(config={"host": ["https://srv-bad", "https://srv-good"],
                                          "skip_detection": True})
        result = tx.translate("Hello", target="es", source="en")
        self.assertEqual(result, "Hola")

    @patch("requests.get")
    def test_translate_timeout_failover(self, mock_get):
        """Timeout from first server must try the next."""
        good = Mock(ok=True, status_code=200, text="Bonjour")
        mock_get.side_effect = [requests.exceptions.Timeout, good]
        tx = OVOSTranslateServer(config={"host": ["https://srv-slow", "https://srv-fast"],
                                          "skip_detection": True})
        result = tx.translate("Hello", target="fr", source="en")
        self.assertEqual(result, "Bonjour")

    @patch("requests.get")
    def test_translate_all_down_raises(self, mock_get):
        """All servers failing must raise RuntimeError."""
        mock_get.side_effect = requests.exceptions.Timeout
        tx = OVOSTranslateServer(config={"host": ["https://srv1", "https://srv2"],
                                          "skip_detection": True})
        with self.assertRaises(RuntimeError):
            tx.translate("Hello", target="es", source="en")

    @patch("requests.get")
    def test_detect_5xx_in_translate_triggers_server_failover(self, mock_get):
        """When /detect returns 5xx, translate should skip to next server entirely."""
        detect_bad = Mock(ok=False, status_code=503)
        detect_good = Mock(ok=True, status_code=200,
                           json=Mock(return_value=["en"]), text="en")
        translate_good = Mock(ok=True, status_code=200, text="Olá")
        mock_get.side_effect = [detect_bad, detect_good, translate_good]
        tx = OVOSTranslateServer(config={"host": ["https://srv-bad", "https://srv-good"]})
        result = tx.translate("Hello", target="pt")
        self.assertEqual(result, "Olá")


if __name__ == "__main__":
    unittest.main()
