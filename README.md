# ovos-translate-server-plugin

An OVOS plugin for language detection and translation. It sends requests to [ovos-translate-server](https://github.com/OpenVoiceOS/ovos-translate-server) and returns the result. The server does the work. This plugin is the client.

It registers two OVOS plugin manager entry points:

- `ovos-lang-detector-plugin-server`: detects the language of a text.
- `ovos-translate-plugin-server`: translates text into a target language.

Other OVOS components use these plugins to translate utterances and texts on demand, for example [solvers](https://openvoiceos.github.io/ovos-technical-manual/solvers/) and [ovos-bidirectional-translation-plugin](https://github.com/OpenVoiceOS/ovos-bidirectional-translation-plugin).

## Install

```bash
pip install ovos-translate-server-plugin
```

## Usage

Add this to your OVOS configuration file (for example `~/.config/mycroft/mycroft.conf`):

```javascript
"language": {
    "detection_module": "ovos-lang-detector-plugin-server",
    "translation_module": "ovos-translate-plugin-server",
    "ovos-lang-detector-plugin-server": {
        "host": "http://24.199.127.142:9686"
    },
    "ovos-translate-plugin-server": {
        "host": "http://24.199.127.142:9686"
    }
}
```

The `host` key sets the server address. It takes a single URL or a list of URLs. Give a list to spread requests across several servers and to add a fallback if one server goes down.

If you omit `host`, the plugin uses its own list of public servers.

Other config keys:

- `timeout`: request timeout in seconds. Default: 5.
- `skip_detection` (translation plugin only): skip automatic source-language detection when no source language is given. Default: false.

## Related projects

- [ovos-translate-server](https://github.com/OpenVoiceOS/ovos-translate-server): the server this plugin talks to.
- [ovos-bidirectional-translation-plugin](https://github.com/OpenVoiceOS/ovos-bidirectional-translation-plugin): a consumer of this plugin.
- [ovos-plugin-manager](https://github.com/OpenVoiceOS/ovos-plugin-manager): the plugin framework this project implements.

## License

Apache-2.0
