# pylint: disable=missing-docstring,redefined-outer-name,protected-access
"""Unit tests for the server_type universal adapter (mocked HTTP)."""
from unittest.mock import patch, MagicMock

import pytest

from ovos_translate_server_plugin import OVOSTranslateServer


def _resp(ok=True, status=200, json_data=None) -> MagicMock:
    r = MagicMock()
    r.ok = ok
    r.status_code = status
    r.text = ""
    if json_data is not None:
        r.json.return_value = json_data
    return r


def test_default_server_type_is_ovos():
    assert OVOSTranslateServer().server_type == "ovos"


def test_libretranslate_request_shape():
    tx = OVOSTranslateServer(config={"server_type": "libretranslate",
                                     "host": "http://localhost:5000",
                                     "api_key": "lt-test"})
    with patch("ovos_translate_server_plugin.requests.post",
               return_value=_resp(json_data={"translatedText": "hola mundo"})) as post:
        out = tx.translate("hello world", target="es", source="en")
    assert out == "hola mundo"
    args, kwargs = post.call_args
    assert args[0] == "http://localhost:5000/translate"
    assert kwargs["data"]["q"] == "hello world"
    assert kwargs["data"]["source"] == "en"
    assert kwargs["data"]["target"] == "es"
    assert kwargs["data"]["api_key"] == "lt-test"


def test_libretranslate_source_defaults_to_auto():
    tx = OVOSTranslateServer(config={"server_type": "libretranslate",
                                     "host": "http://localhost:5000"})
    with patch("ovos_translate_server_plugin.requests.post",
               return_value=_resp(json_data={"translatedText": "hola"})) as post:
        tx.translate("hello", target="es")
    assert post.call_args.kwargs["data"]["source"] == "auto"


def test_deepl_request_shape():
    tx = OVOSTranslateServer(config={"server_type": "deepl",
                                     "host": "https://api-free.deepl.com",
                                     "api_key": "dl-test"})
    with patch("ovos_translate_server_plugin.requests.post",
               return_value=_resp(json_data={"translations": [{"text": "Hallo Welt"}]})) as post:
        out = tx.translate("hello world", target="de", source="en")
    assert out == "Hallo Welt"
    args, kwargs = post.call_args
    assert args[0] == "https://api-free.deepl.com/v2/translate"
    assert kwargs["headers"]["Authorization"] == "DeepL-Auth-Key dl-test"
    # DeepL expects upper-case language codes
    assert kwargs["data"]["target_lang"] == "DE"
    assert kwargs["data"]["source_lang"] == "EN"


def test_vendor_type_requires_host():
    tx = OVOSTranslateServer(config={"server_type": "libretranslate"})
    with pytest.raises(RuntimeError):
        tx.translate("hello", target="es")


def test_unknown_server_type_raises():
    tx = OVOSTranslateServer(config={"server_type": "bogus", "host": "http://localhost:5000"})
    with pytest.raises(RuntimeError):
        tx.translate("hello", target="es")
