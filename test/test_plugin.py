import unittest
from unittest.mock import patch, Mock

from ovos_translate_server_plugin import OVOSTranslateServer, OVOSLangDetectServer


class TestOVOSLangDetectServer(unittest.TestCase):

    @patch('requests.get')
    def test_detect(self, mock_get):
        dt = OVOSLangDetectServer()

        # Mock response for the language detection request
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = ["en"]
        mock_get.return_value = mock_response

        # Test language detection
        text = "Hello, world!"
        detected_language = dt.detect(text)
        self.assertEqual(detected_language, "en")

    @patch('requests.get')
    def test_detect_probs(self, mock_get):
        dt = OVOSLangDetectServer()

        # Mock response for the language detection probabilities request
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"en": 0.95, "es": 0.05}
        mock_get.return_value = mock_response

        # Test language detection probabilities
        text = "Hello, world!"
        detected_probs = dt.detect_probs(text)
        self.assertEqual(detected_probs, {"en": 0.95, "es": 0.05})

    def test_get_servers(self):
        dt = OVOSLangDetectServer()

        # Test when host is specified
        dt.host = "https://custom.server"
        self.assertEqual(dt.get_servers(), ["https://custom.server"])

        # Test when host is not specified
        dt.host = None
        servers = dt.get_servers()
        self.assertIn("https://nllb.openvoiceos.org", servers)
        self.assertIn("https://translator.smartgic.io/nllb", servers)


class TestOVOSTranslateServer(unittest.TestCase):

    @patch('requests.get')
    def test_translate(self, mock_get):
        tx = OVOSTranslateServer()

        # Mock response for the translation request
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = "Hello, world!"
        mock_get.return_value = mock_response

        # Test translation
        text = "Hola Mundo"
        translated_text = tx.translate(text, target="en", source="es")
        self.assertEqual(translated_text, "Hello, world!")

    @patch('requests.get')
    def test_translate_without_source(self, mock_get):
        tx = OVOSTranslateServer()

        # Mock responses for the language detection and translation requests
        mock_response_detect = Mock()
        mock_response_detect.ok = True
        mock_response_detect.json.return_value = ["es"]
        mock_response_translate = Mock()
        mock_response_translate.ok = True
        mock_response_translate.text = "Hello, world!"
        mock_get.side_effect = [mock_response_detect, mock_response_translate]

        # Test translation without specifying source language
        text = "Hola Mundo"
        translated_text = tx.translate(text, target="en")
        self.assertEqual(translated_text, "Hello, world!")

    def test_get_servers(self):
        tx = OVOSTranslateServer()

        # Test when host is specified
        tx.host = "https://custom.server"
        self.assertEqual(tx.get_servers(), ["https://custom.server"])

        # Test when host is not specified
        tx.host = None
        servers = tx.get_servers()
        self.assertIn("https://nllb.openvoiceos.org", servers)
        self.assertIn("https://translator.smartgic.io/nllb", servers)
        self.assertIn("https://ovosnllb.ziggyai.online", servers)


if __name__ == "__main__":
    unittest.main()
