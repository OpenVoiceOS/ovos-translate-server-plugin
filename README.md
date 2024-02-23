Language Plugin for [ovos translate server](https://github.com/OpenVoiceOS/ovos-translate-server)

## Usage

### OVOS

The plugin is used in a wider context to translate utterances/texts on demand (e.g. from [solvers](https://openvoiceos.github.io/ovos-technical-manual/solvers/) and [ovos-bidirectional-translation-plugin](https://github.com/OpenVoiceOS/ovos-bidirectional-translation-plugin))

add this to one of the configuration files (eg `~./config/mycroft/mycroft.conf`)

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
