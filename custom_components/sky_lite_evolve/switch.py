"""Switch platform for Sky Lite Evolve (laser on/off, motor on/off)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SkyLiteEvolveConfigEntry
from .const import DOMAIN, DPS_LASER_STATE, DPS_MOTOR_STATE, DPS_POWER
from .coordinator import SkyLiteEvolveCoordinator


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: SkyLiteEvolveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sky Lite Evolve switches from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            SkyLiteEvolveLaserSwitch(coordinator, entry),
            SkyLiteEvolveMotorSwitch(coordinator, entry),
        ]
    )


class SkyLiteEvolveLaserSwitch(
    CoordinatorEntity[SkyLiteEvolveCoordinator], SwitchEntity
):
    """Switch to control the laser on/off."""

    _attr_has_entity_name = True
    _attr_translation_key = "laser"

    def __init__(
        self,
        coordinator: SkyLiteEvolveCoordinator,
        entry: SkyLiteEvolveConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_laser_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the laser is on."""
        if self.coordinator.data is None:
            return None
        power = self.coordinator.data.get(DPS_POWER)
        laser = self.coordinator.data.get(DPS_LASER_STATE)
        if power is None or laser is None:
            return None
        return bool(power) and bool(laser)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the laser on."""
        commands: dict[str, Any] = {}
        if not self.coordinator.data.get(DPS_POWER):
            commands[DPS_POWER] = True
        commands[DPS_LASER_STATE] = True
        await self.coordinator.async_send_commands(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the laser off."""
        await self.coordinator.async_send_command(DPS_LASER_STATE, False)


class SkyLiteEvolveMotorSwitch(
    CoordinatorEntity[SkyLiteEvolveCoordinator], SwitchEntity
):
    """Switch to control the motor/rotation on/off."""

    _attr_has_entity_name = True
    _attr_translation_key = "motor"

    def __init__(
        self,
        coordinator: SkyLiteEvolveCoordinator,
        entry: SkyLiteEvolveConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_motor_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the motor is on."""
        if self.coordinator.data is None:
            return None
        power = self.coordinator.data.get(DPS_POWER)
        motor = self.coordinator.data.get(DPS_MOTOR_STATE)
        if power is None or motor is None:
            return None
        return bool(power) and bool(motor)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the motor on."""
        commands: dict[str, Any] = {}
        if not self.coordinator.data.get(DPS_POWER):
            commands[DPS_POWER] = True
        commands[DPS_MOTOR_STATE] = True
        await self.coordinator.async_send_commands(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the motor off."""
        await self.coordinator.async_send_command(DPS_MOTOR_STATE, False)
