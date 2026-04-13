# BlissLights Sky Lite Evolve - Home Assistant Integration

A custom Home Assistant integration for the [BlissLights Sky Lite Evolve](https://blisslights.com/products/skylite-evolve) star projector, supporting both Tuya Cloud API and local control via tinytuya.

## Features

- **Nebula light** - On/off, color (hue/saturation), brightness
- **Laser switch** - On/off
- **Motor switch** - On/off (nebula rotation motor)
- **Laser brightness** - Slider (1-100%)
- **Rotation speed** - Slider (1-100%)
- **Dual connection modes** - Tuya Cloud API or local LAN (tinytuya, protocol v3.5)

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS
2. Search for "BlissLights Sky Lite Evolve" and install
3. Restart Home Assistant
4. Go to Settings > Devices & Services > Add Integration > "BlissLights Sky Lite Evolve"

### Manual

1. Copy `custom_components/sky_lite_evolve/` into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to Settings > Devices & Services > Add Integration > "BlissLights Sky Lite Evolve"

## Configuration

### Tuya Cloud API (recommended for getting started)

You'll need credentials from a [Tuya IoT Platform](https://iot.tuya.com/) project:

1. **Access Key** - From your Tuya IoT Cloud project
2. **Secret Key** - From your Tuya IoT Cloud project
3. **Device ID** - Your projector's virtual device ID
4. **Region** - US West, US East, EU Central, EU West, China, or India

Set up the device through the **Tuya Smart** app (not the BlissHome app), then link it to a Tuya IoT Cloud project. See the [Tuya IoT Platform docs](https://developer.tuya.com/en/docs/iot/quick-start1?id=K95ztz9u9t89n) for details.

### Local Connection (tinytuya)

For local LAN control without cloud dependency:

1. **Access Key** / **Secret Key** - From your Tuya IoT Cloud project (used once to fetch the local key)
2. **Device ID** - Your projector's Tuya device ID
3. **Region** - US West, US East, EU Central, EU West, China, or India
4. **IP Address** - Your projector's **local LAN IP** (e.g. `192.168.1.x`), not your public/ISP address

The integration automatically fetches the local encryption key from the Tuya cloud during setup. Cloud credentials are not stored — only the device ID, local key, and IP address are saved.

**Finding your device's local IP:**
- Check your router's admin page for connected devices — the Evolve may appear as **"lwip0"**
- The Tuya Smart app shows the device's MAC address (Device > Edit > Device Information), which can help identify it in your router's client list
- Or run `python3 -m tinytuya scan` from a machine on the same network

> **Tip:** Set a static IP / DHCP reservation for the device in your router. tinytuya connects to a fixed IP and won't track changes from DHCP.

The Evolve uses Tuya local protocol **v3.5** (handled automatically by the integration).

## Development

### Prerequisites

- Docker
- Python 3.14.2+ (managed via pyenv — the Makefile handles installation)

### VS Code Devcontainer

This is the standard HA development workflow, matching the [integration_blueprint](https://github.com/ludeeus/integration_blueprint) template.

1. Open the repo in VS Code
2. When prompted, click "Reopen in Container" (or Cmd+Shift+P > "Dev Containers: Reopen in Container")
3. Wait for the container to build and `scripts/setup` to install deps
4. Run `scripts/develop` (or `make develop`) to start HA with the integration loaded
5. Open http://localhost:8123, complete onboarding, add the integration
6. Edit code, restart HA to pick up changes (or Reload for entity-only changes)

### Linting and formatting

```bash
make lint       # Run ruff linter
make format     # Run ruff formatter
make check      # Run all checks (lint + format)
```

### Testing

Tests use [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component), the standard testing framework for HA custom integrations.

```bash
make test       # Run tests
make test-cov   # Run tests with coverage report
```

### All make targets

```
make help       # Show all targets
make develop    # Run HA with integration loaded
make setup      # Install deps (used by devcontainer postCreateCommand)
make lint       # Run ruff linter
make format     # Run ruff formatter
make check      # Run all checks (lint + format)
make test       # Run tests
make test-cov   # Run tests with coverage
make clean      # Remove local venv
```

### Python version

This project tracks Home Assistant's required Python version (currently **3.14.2**, pinned in `.python-version`). The ruff and devcontainer configs also target Python 3.14.

### Project structure

```
.devcontainer.json          # VS Code devcontainer config
.github/workflows/          # CI: lint (ruff), validate (hassfest + HACS)
.ruff.toml                  # Ruff config (mirrors HA core)
scripts/setup               # Install deps (devcontainer postCreateCommand)
scripts/develop             # Start HA with integration loaded
config/configuration.yaml   # Dev HA config (debug logging enabled)
custom_components/
  sky_lite_evolve/
    __init__.py             # Integration setup (runtime_data pattern)
    config_flow.py          # UI config flow (cloud + local steps)
    const.py                # Constants, DPS codes, cloud command codes
    coordinator.py          # DataUpdateCoordinator (30s poll)
    tuya_api.py             # Cloud + local API clients
    light.py                # Nebula LED entity
    switch.py               # Laser + motor on/off entities
    number.py               # Laser brightness + rotation speed entities
    manifest.json           # HA integration manifest
    strings.json            # UI strings + entity translations
    translations/en.json    # English translations
    brand/icon.png          # Integration icon (256x256)
tests/
  conftest.py               # Test fixtures (mock API clients, config entries)
  test_config_flow.py       # Config flow tests (cloud, local, errors, dupes)
```

## Architecture

The integration uses a `DataUpdateCoordinator` that polls device state every 30 seconds. Both connection backends (`TuyaCloudApi` and `TuyaLocalDevice`) expose the same interface, so entities work identically regardless of connection type.

Internally, all state is normalized to Tuya DPS (Data Point Schema) keys. The cloud API translates between Tuya's `code`/`value` format and DPS numbers transparently.

### DPS mapping (Sky Lite Evolve)

| DPS | Function | Values |
|-----|----------|--------|
| 20  | Power | `true`/`false` |
| 24  | Color | HSV hex (`HHHHSSSSVVVV`) — brightness is the V component |
| 51  | Mode | `colour`, `laser` |
| 52  | Color LED state | `true`/`false` |
| 53  | Laser state | `true`/`false` |
| 54  | Laser brightness | 10-1000 |
| 60  | Motor state | `true`/`false` |
| 62  | Rotation speed | 1-100 |

## Credits

- [homebridge-sky-lite-evolve](https://github.com/kevbo/homebridge-sky-lite-evolve) - Original Homebridge plugin (Tuya Cloud API)
- [homebridge-blisslights](https://github.com/traviswparker/homebridge-blisslights) - Fork with Evolve local support and DPS mapping
- [homebridge-star-projector](https://github.com/seydx/homebridge-star-projector) - Original star projector plugin by seydx
- [integration_blueprint](https://github.com/ludeeus/integration_blueprint) - HA custom integration template

## License

MIT
