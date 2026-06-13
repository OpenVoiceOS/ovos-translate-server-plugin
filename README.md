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

### Universal adapter (`server_type`)

By default the plugin talks to a native `ovos-translate-server`
(`server_type: "ovos"`). Set `server_type` to target any other compatible
translation API — the plugin becomes a universal adapter:

```javascript
"language": {
    "translation_module": "ovos-translate-plugin-server",
    "ovos-translate-plugin-server": {
        "server_type": "deepl",
        "host": "https://api-free.deepl.com",
        "api_key": "..."
    }
}
```

| `server_type` | Endpoint used | `host` example | Notes |
|---|---|---|---|
| `ovos` (default) | `/translate/{src}/{tgt}/{text}` | `http://host:9686` | native ovos-translate-server |
| `libretranslate` | `POST /translate` | `http://localhost:5000` | any self-hosted/hosted LibreTranslate (`api_key` optional) |
| `deepl` | `POST /v2/translate` | `https://api-free.deepl.com` | `api_key` → `Authorization: DeepL-Auth-Key` |

For vendor server types an explicit `host` is required.
