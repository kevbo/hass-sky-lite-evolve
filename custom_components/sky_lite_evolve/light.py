"""Light platform for Sky Lite Evolve (nebula/color LED)."""

from __future__ import annotations

import json
from typing import Any, ClassVar

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SkyLiteEvolveConfigEntry
from .const import (
    DOMAIN,
    DPS_COLOR,
    DPS_COLOR_STATE,
    DPS_POWER,
)
from .coordinator import SkyLiteEvolveCoordinator

_COLOUR_DATA_HEX_LEN = 12


def _parse_colour_data(value: Any) -> tuple[int, int, int]:
    """
    Parse colour_data from hex string, JSON string, or dict.

    Local format: hex string "HHHHSSSSVVVV" (4 hex chars each)
    Cloud format: JSON string or dict {"h": 0-360, "s": 0-1000, "v": 0-1000}
    Returns: (h, s, v) as raw Tuya values.
    """
    if isinstance(value, dict):
        return (
            int(value.get("h", 0)),
            int(value.get("s", 1000)),
            int(value.get("v", 1000)),
        )
    if not isinstance(value, str):
        return (0, 1000, 1000)
    # Try hex first (12 hex chars = 3 x 4)
    if len(value) == _COLOUR_DATA_HEX_LEN:
        try:
            h = int(value[0:4], 16)
            s = int(value[4:8], 16)
            v = int(value[8:12], 16)
        except ValueError:
            pass
        else:
            return (h, s, v)
    # Try JSON
    try:
        d = json.loads(value)
        if isinstance(d, dict):
            return (int(d.get("h", 0)), int(d.get("s", 1000)), int(d.get("v", 1000)))
    except json.JSONDecodeError, TypeError:
        pass
    return (0, 1000, 1000)


def _make_colour_data(h: int, s: int, v: int) -> dict[str, int]:
    """Create colour_data as a dict. The API layer handles encoding."""
    return {"h": h, "s": s, "v": v}


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: SkyLiteEvolveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sky Lite Evolve light from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([SkyLiteEvolveLight(coordinator, entry)])


class SkyLiteEvolveLight(CoordinatorEntity[SkyLiteEvolveCoordinator], LightEntity):
    """Representation of the Sky Lite Evolve nebula light."""

    _attr_has_entity_name = True
    _attr_translation_key = "nebula"
    _attr_supported_color_modes: ClassVar[set[ColorMode]] = {ColorMode.HS}
    _attr_color_mode = ColorMode.HS

    def __init__(
        self,
        coordinator: SkyLiteEvolveCoordinator,
        entry: SkyLiteEvolveConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_nebula_light"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name=entry.title,
            manufacturer="BlissLights",
            model="Sky Lite Evolve",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the nebula light is on."""
        if self.coordinator.data is None:
            return None
        power = self.coordinator.data.get(DPS_POWER)
        color_state = self.coordinator.data.get(DPS_COLOR_STATE)
        if power is None:
            return None
        if color_state is not None:
            return bool(power) and bool(color_state)
        return bool(power)

    @property
    def brightness(self) -> int | None:
        """Return the brightness (from colour_data V, 0-1000 -> 0-255)."""
        color_data = (
            self.coordinator.data.get(DPS_COLOR) if self.coordinator.data else None
        )
        if color_data is not None:
            _, _, v = _parse_colour_data(color_data)
            return max(1, round(v / 1000 * 255))
        return None

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the HS color."""
        color_data = (
            self.coordinator.data.get(DPS_COLOR) if self.coordinator.data else None
        )
        if color_data is not None:
            h, s, _ = _parse_colour_data(color_data)
            return (float(h), round(s / 10))
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the nebula light on."""
        commands: dict[str, Any] = {}

        if not self.coordinator.data.get(DPS_POWER):
            commands[DPS_POWER] = True

        commands[DPS_COLOR_STATE] = True

        # Get current HSV from colour_data
        current = (
            self.coordinator.data.get(DPS_COLOR) if self.coordinator.data else None
        )
        cur_h, cur_s, cur_v = (
            _parse_colour_data(current) if current else (0, 1000, 1000)
        )

        new_h, new_s, new_v = cur_h, cur_s, cur_v

        if ATTR_HS_COLOR in kwargs:
            new_h = int(kwargs[ATTR_HS_COLOR][0])
            new_s = int(kwargs[ATTR_HS_COLOR][1] * 10)

        if ATTR_BRIGHTNESS in kwargs:
            new_v = max(10, int(kwargs[ATTR_BRIGHTNESS] / 255 * 1000))

        if ATTR_HS_COLOR in kwargs or ATTR_BRIGHTNESS in kwargs:
            commands[DPS_COLOR] = _make_colour_data(new_h, new_s, new_v)

        await self.coordinator.async_send_commands(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the nebula light off."""
        await self.coordinator.async_send_command(DPS_COLOR_STATE, False)
