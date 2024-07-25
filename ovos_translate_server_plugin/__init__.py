import random
from typing import Union, List, Dict, Optional

import requests
from ovos_plugin_manager.templates.language import LanguageDetector, LanguageTranslator


class OVOSLangDetectServer(LanguageDetector):
    PUBLIC_MODEL = "ovos-lang-detector-fasttext-plugin"  # manually maintained, public servers need to respect this to get added to list
    public_servers = [
        "https://nllb.openvoiceos.org",
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
                # call lang detect endpoint
                r = requests.get(f'{url}/detect/{text}')
                if r.ok:
                    try:
                        return r.json()[0]
                    except:
                        return r.text
            except:
                continue
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
                # call lang detect endpoint
                r = requests.get(f'{url}/classify/{text}')
                if r.ok:
                    return r.json()
            except:
                continue
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


class OVOSTranslateServer(LanguageTranslator):
    PUBLIC_MODEL = "ovos-translate-plugin-nllb"  # manually maintained, public servers need to respect this to get added to list
    public_servers = [
        "https://nllb.openvoiceos.org",
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
            try:
                if not source and not self.skip_detection:
                    # call lang detect endpoint
                    r = requests.get(f'{url}/detect/{text}')
                    try:
                        source = r.json()[0]
                    except:
                        source = r.text

                if source:
                    u = f'{url}/translate/{source}/{target}/{text}'
                else:
                    # let the server plugin determine source lang by itself
                    u = f'{url}/translate/{target}/{text}'

                r = requests.get(u)
                if r.ok:
                    return r.text
            except:
                continue
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
