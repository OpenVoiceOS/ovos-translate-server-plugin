Language Plugin for [ovos translate server](https://github.com/OpenVoiceOS/ovos-translate-server)

## Usage

### OVOS

The plugin is used in a wider context to translate utterances/texts on demand (e.g. from [ovos-bidirectional-translation-plugin](https://github.com/OpenVoiceOS/ovos-bidirectional-translation-plugin))

_Configuration_
```python
# add this to one of the configuration files (eg ~./config/mycroft/mycroft.conf)

"language": {
    "translation_module": "ovos-translate-plugin-server",
    "ovos-translate-plugin-server": {
        "host": "http://24.199.127.142:9686"
    }
}

```
