import random
from typing import Union, List

import requests
from ovos_plugin_manager.templates.language import LanguageTranslator
from ovos_utils.log import LOG


class OVOSTranslateServer(LanguageTranslator):
    public_servers = [
        "https://nllb.openvoiceos.org",
        "https://translator.smartgic.io/nllb",
        "https://ovosnllb.ziggyai.online"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = self.config.get("host", None)
        # detect source lang before making query
        self.skip_detection = self.config.get("skip_detection", False)

    def translate(self,
                  text: Union[str, List[str]],
                  target: str = "",
                  source: str = "") -> Union[str, List[str]]:
        """
        NLLB200 translate text(s) into the target language.

        Args:
            text (Union[str, List[str]]): sentence(s) to translate
            target (str, optional): target langcode. Defaults to "".
            source (str, optional): source langcode. Defaults to "".

        Returns:
            Union[str, List[str]]: translation(s)
        """
        if self.host:
            if isinstance(self.host, str):
                servers = [self.host]
            else:
                servers = self.host
        else:
            servers = self.public_servers
            random.shuffle(servers)  # Spread the load among all public servers

        return self._get_from_servers(servers, text, target, source)

    def _get_from_servers(self, servers: list, text: str,
                          target: str = "",
                          source: str = ""):
        target = target or self.internal_language

        text = text.replace("/", "-")  # HACK - if text has a / the url is invalid
        for url in servers:
            try:
                if not source and not self.skip_detection:
                    # call lang detect endpoint
                    r = requests.get(f'{url}/detect/{text}')
                    try:
                        source = r.json()[0]
                    except:
                        source = r.text
                    LOG.debug(f"detected language: {source}")

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
        raise RuntimeError(f"All OVOS Translate servers are down!")


if __name__ == "__main__":
    src = "es"
    tgt = "en-us"

    tx = OVOSTranslateServer()

    utts = "Hola Mundo"

    print("Translations:", tx.translate(utts, tgt, src))
    print("Translations:", tx.translate(utts, tgt))

    utts = "hello world"

    print("Translations:", tx.translate(utts, src, tgt))
