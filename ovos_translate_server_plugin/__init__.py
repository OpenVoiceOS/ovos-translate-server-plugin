import random
import requests
from ovos_plugin_manager.templates.language import LanguageDetector, LanguageTranslator
from ovos_utils import classproperty
from ovos_utils.log import LOG
from typing import Union, List, Dict, Optional, Set

_DEFAULT_TIMEOUT = 5  # seconds


class OVOSLangDetectServer(LanguageDetector):
    PUBLIC_MODEL = "ovos-lang-detector-fasttext-plugin"  # manually maintained, public servers need to respect this to get added to list
    public_servers = [
        "https://nllb.tigregotico.pt",
        "https://translator.smartgic.io/nllb",
        # "https://ovosnllb.ziggyai.online"  # TODO - not yet using fasttext, needs to update container
    ]

    def __init__(self, *args, **kwargs):
        """
        Initialize the language detection server.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.host: Optional[Union[str, List[str]]] = self.config.get("host", None)

    @property
    def timeout(self) -> int:
        """Request timeout in seconds (config key ``timeout``, default 20)."""
        return self.config.get("timeout", _DEFAULT_TIMEOUT)

    def detect(self, text: str) -> str:
        """
        Detect the language of the given text.

        Args:
            text (str): Text to detect the language for.

        Returns:
            str: Detected language code.
        """
        text = text.replace("/", "-")  # HACK - if text has a / the url is invalid
        for url in self.get_servers():
            try:
                r = requests.get(f'{url}/detect/{text}', timeout=self.timeout)
                if r.status_code >= 500:
                    LOG.warning(f"Server error {r.status_code} from {url}/detect — trying next server")
                    continue
                if r.ok:
                    try:
                        return r.json()[0]
                    except Exception:
                        return r.text
            except requests.exceptions.Timeout:
                LOG.warning(f"Timeout contacting {url}/detect — trying next server")
            except Exception:
                LOG.exception(f"Error contacting {url}/detect")
        raise RuntimeError("All OVOS Translate servers are down!")

    def detect_probs(self, text: str) -> Dict[str, float]:
        """
        Detect the language probabilities for the given text.

        Args:
            text (str): Text to detect the language probabilities for.

        Returns:
            Dict[str, float]: Dictionary of language codes and their probabilities.
        """
        text = text.replace("/", "-")  # HACK - if text has a / the url is invalid
        for url in self.get_servers():
            try:
                r = requests.get(f'{url}/classify/{text}', timeout=self.timeout)
                if r.status_code >= 500:
                    LOG.warning(f"Server error {r.status_code} from {url}/classify — trying next server")
                    continue
                if r.ok:
                    return r.json()
            except requests.exceptions.Timeout:
                LOG.warning(f"Timeout contacting {url}/classify — trying next server")
            except Exception:
                LOG.exception(f"Error contacting {url}/classify")
        raise RuntimeError("All OVOS Translate servers are down!")

    def get_servers(self) -> List[str]:
        """
        Get the list of servers to use for language detection.

        Returns:
            List[str]: List of server URLs.
        """
        if self.host:
            if isinstance(self.host, str):
                servers = [self.host]
            else:
                servers = self.host
        else:
            servers = self.public_servers
            random.shuffle(servers)  # Spread the load among all public servers
        return servers

    @classproperty
    def available_languages(cls) -> Set[str]:
        """
        Get the available target languages with the service.

        Returns:
            Set[str]: A set of language codes.
        """
        return set()


class OVOSTranslateServer(LanguageTranslator):
    PUBLIC_MODEL = "ovos-translate-plugin-nllb"  # manually maintained, public servers need to respect this to get added to list
    public_servers = [
        "https://nllb.tigregotico.pt",
        "https://translator.smartgic.io/nllb",
        "https://ovosnllb.ziggyai.online"
    ]

    def __init__(self, *args, **kwargs):
        """
        Initialize the translation server.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.host: Optional[Union[str, List[str]]] = self.config.get("host", None)
        self.skip_detection: bool = self.config.get("skip_detection", False)

    @property
    def timeout(self) -> int:
        """Request timeout in seconds (config key ``timeout``, default 20)."""
        return self.config.get("timeout", _DEFAULT_TIMEOUT)

    def translate(self,
                  text: Union[str, List[str]],
                  target: str = "",
                  source: str = "") -> Union[str, List[str]]:
        """
        NLLB200 translate text(s) into the target language.

        Args:
            text (Union[str, List[str]]): Sentence(s) to translate.
            target (str, optional): Target language code. Defaults to "".
            source (str, optional): Source language code. Defaults to "".

        Returns:
            Union[str, List[str]]: Translation(s).
        """
        target = target or self.internal_language

        text = text.replace("/", "-")  # HACK - if text has a / the url is invalid
        for url in self.get_servers():
            source_for_url = source  # don't mutate outer `source` across servers
            try:
                if not source_for_url and not self.skip_detection:
                    r = requests.get(f'{url}/detect/{text}', timeout=self.timeout)
                    if r.status_code >= 500:
                        LOG.warning(f"Server error {r.status_code} from {url}/detect — trying next server")
                        continue
                    try:
                        source_for_url = r.json()[0]
                    except Exception:
                        source_for_url = r.text

                if source_for_url:
                    u = f'{url}/translate/{source_for_url}/{target}/{text}'
                else:
                    # let the server plugin determine source lang by itself
                    u = f'{url}/translate/{target}/{text}'

                r = requests.get(u, timeout=self.timeout)
                if r.status_code >= 500:
                    LOG.warning(f"Server error {r.status_code} from {url}/translate — trying next server")
                    continue
                if r.ok:
                    return r.text
            except requests.exceptions.Timeout:
                LOG.warning(f"Timeout contacting {url} — trying next server")
            except Exception:
                LOG.exception(f"Error contacting {url}")
        raise RuntimeError("All OVOS Translate servers are down!")

    def get_servers(self) -> List[str]:
        """
        Get the list of servers to use for translation.

        Returns:
            List[str]: List of server URLs.
        """
        if self.host:
            if isinstance(self.host, str):
                servers = [self.host]
            else:
                servers = self.host
        else:
            servers = self.public_servers
            random.shuffle(servers)  # Spread the load among all public servers
        return servers

    @classproperty
    def available_languages(cls) -> Set[str]:
        """
        Get the available target languages with the service.

        Returns:
            Set[str]: A set of language codes.
        """
        return set()

    def supported_translations(self, source_lang: str) -> Set[str]:
        """
        Get the set of target languages to which the source language can be translated.

        Args:
            source_lang (Optional[str]): The source language code.

        Returns:
            Set[str]: A set of language codes that the source language can be translated to.
        """
        return self.available_languages


if __name__ == "__main__":
    dt = OVOSLangDetectServer()

    src = "es"
    tgt = "en-us"

    tx = OVOSTranslateServer()

    utts = "Hola Mundo"

    print("Detections: ", dt.detect_probs(utts))
    print("Translations:", tx.translate(utts, tgt, src))
    print("Translations:", tx.translate(utts, tgt))

    utts = "hello world"

    print("Detections: ", dt.detect_probs(utts))
    print("Translations:", tx.translate(utts, src, tgt))
