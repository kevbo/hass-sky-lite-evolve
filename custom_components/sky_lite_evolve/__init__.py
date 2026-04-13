"""The Sky Lite Evolve integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID
from .const import DOMAIN as DOMAIN
from .coordinator import SkyLiteEvolveCoordinator
from .tuya_api import TuyaCloudApi, create_api_client

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.SWITCH, Platform.NUMBER]

type SkyLiteEvolveConfigEntry = ConfigEntry[SkyLiteEvolveCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: SkyLiteEvolveConfigEntry
) -> bool:
    """Set up Sky Lite Evolve from a config entry."""
    api = create_api_client(hass, dict(entry.data))

    # Log device specification to discover correct command codes
    if isinstance(api, TuyaCloudApi):
        try:
            spec = await api.get_device_specification()
            _LOGGER.info("Device specification: %s", spec)
        except (OSError, ValueError) as err:
            _LOGGER.warning("Could not fetch device specification: %s", err)

    coordinator = SkyLiteEvolveCoordinator(hass, api, entry.data[CONF_DEVICE_ID])

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SkyLiteEvolveConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await entry.runtime_data.api.close()

    return unload_ok
