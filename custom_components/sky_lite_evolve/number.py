"""Number platform for Sky Lite Evolve (laser brightness, rotation speed)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SkyLiteEvolveConfigEntry
from .const import (
    DOMAIN,
    DPS_LASER_BRIGHTNESS,
    DPS_ROTATION,
    LASER_BRIGHTNESS_MAX,
    LASER_BRIGHTNESS_MIN,
    ROTATION_SPEED_MAX,
    ROTATION_SPEED_MIN,
)
from .coordinator import SkyLiteEvolveCoordinator


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: SkyLiteEvolveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sky Lite Evolve number entities from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            SkyLiteEvolveLaserBrightness(coordinator, entry),
            SkyLiteEvolveRotationSpeed(coordinator, entry),
        ]
    )


class SkyLiteEvolveLaserBrightness(
    CoordinatorEntity[SkyLiteEvolveCoordinator], NumberEntity
):
    """Number entity for laser brightness (10-1000 mapped to 1-100%)."""

    _attr_has_entity_name = True
    _attr_translation_key = "laser_brightness"
    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: SkyLiteEvolveCoordinator,
        entry: SkyLiteEvolveConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_laser_brightness"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
        )

    @property
    def native_value(self) -> float | None:
        """Return the current laser brightness as a percentage."""
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(DPS_LASER_BRIGHTNESS)
        if raw is None:
            return None
        return round(int(raw) / 10)

    async def async_set_native_value(self, value: float) -> None:
        """Set the laser brightness."""
        raw = int(value * 10)
        raw = max(LASER_BRIGHTNESS_MIN, min(LASER_BRIGHTNESS_MAX, raw))
        await self.coordinator.async_send_command(DPS_LASER_BRIGHTNESS, raw)


class SkyLiteEvolveRotationSpeed(
    CoordinatorEntity[SkyLiteEvolveCoordinator], NumberEntity
):
    """Number entity for star rotation speed (1-100)."""

    _attr_has_entity_name = True
    _attr_translation_key = "rotation_speed"
    _attr_native_min_value = ROTATION_SPEED_MIN
    _attr_native_max_value = ROTATION_SPEED_MAX
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: SkyLiteEvolveCoordinator,
        entry: SkyLiteEvolveConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_rotation_speed"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
        )

    @property
    def native_value(self) -> float | None:
        """Return the current rotation speed."""
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(DPS_ROTATION)
        if raw is None:
            return None
        return int(raw)

    async def async_set_native_value(self, value: float) -> None:
        """Set the rotation speed."""
        raw = int(value)
        raw = max(ROTATION_SPEED_MIN, min(ROTATION_SPEED_MAX, raw))
        await self.coordinator.async_send_command(DPS_ROTATION, raw)
