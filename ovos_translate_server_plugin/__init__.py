import random
from typing import Union, List

import requests
from ovos_plugin_manager.templates.language import LanguageTranslator


class OVOSTranslateServer(LanguageTranslator):
    public_servers = [
        "https://translator.smartgic.io/nllb",
        "http://24.199.127.142:9686"  # TODO nllb.openvoice.org domain
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = self.config.get("host", None)

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

        return self._get_from_servers(text, target, source, servers)

    def _get_from_servers(self, text: str,
                          target: str,
                          source: str,
                          servers: list):
        for url in servers:
            try:
                r = requests.get(f'{url}/translate/{source}/{target}/{text}')
                if r.ok:
                    return r.text
            except:
                continue
        raise RuntimeError(f"All OVOS Translate servers are down!")


if __name__ == "__main__":
    src = "es"
    tgt = "en-us"

    tx = OVOSTranslateServer()

    utts = ["Hola Mundo"]

    print("Translations:", tx.translate(utts, tgt, src))

    utts = "hello world"

    print("Translations:", tx.translate(utts, src, tgt))
