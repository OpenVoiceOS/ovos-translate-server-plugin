import unittest
from unittest.mock import patch, Mock

from ovos_translate_server_plugin import OVOSTranslateServer, OVOSLangDetectServer


class TestOVOSLangDetectServer(unittest.TestCase):

    @patch('requests.get')
    def test_detect(self, mock_get):
        dt = OVOSLangDetectServer()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = ["en"]
        mock_get.return_value = mock_response

        detected_language = dt.detect("Hello, world!")
        self.assertEqual(detected_language, "en")

    @patch('requests.get')
    def test_detect_probs(self, mock_get):
        dt = OVOSLangDetectServer()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"en": 0.95, "es": 0.05}
        mock_get.return_value = mock_response

        detected_probs = dt.detect_probs("Hello, world!")
        self.assertEqual(detected_probs, {"en": 0.95, "es": 0.05})

    def test_get_servers(self):
        dt = OVOSLangDetectServer()

        dt.host = "https://custom.server"
        self.assertEqual(dt.get_servers(), ["https://custom.server"])

        dt.host = None
        servers = dt.get_servers()
        self.assertIn("https://nllb.tigregotico.pt", servers)
        self.assertIn("https://translator.smartgic.io/nllb", servers)


class TestOVOSTranslateServer(unittest.TestCase):

    @patch('requests.get')
    def test_translate(self, mock_get):
        tx = OVOSTranslateServer()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.text = "Hello, world!"
        mock_get.return_value = mock_response

        translated_text = tx.translate("Hola Mundo", target="en", source="es")
        self.assertEqual(translated_text, "Hello, world!")

    @patch('requests.get')
    def test_translate_without_source(self, mock_get):
        tx = OVOSTranslateServer()

        mock_response_detect = Mock()
        mock_response_detect.status_code = 200
        mock_response_detect.ok = True
        mock_response_detect.json.return_value = ["es"]
        mock_response_translate = Mock()
        mock_response_translate.status_code = 200
        mock_response_translate.ok = True
        mock_response_translate.text = "Hello, world!"
        mock_get.side_effect = [mock_response_detect, mock_response_translate]

        translated_text = tx.translate("Hola Mundo", target="en")
        self.assertEqual(translated_text, "Hello, world!")

    def test_get_servers(self):
        tx = OVOSTranslateServer()

        tx.host = "https://custom.server"
        self.assertEqual(tx.get_servers(), ["https://custom.server"])

        tx.host = None
        servers = tx.get_servers()
        self.assertIn("https://nllb.tigregotico.pt", servers)
        self.assertIn("https://translator.smartgic.io/nllb", servers)
        self.assertIn("https://ovosnllb.ziggyai.online", servers)


if __name__ == "__main__":
    unittest.main()
