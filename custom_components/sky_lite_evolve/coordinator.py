"""DataUpdateCoordinator for Sky Lite Evolve."""

from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .tuya_api import TuyaCloudApi, TuyaLocalDevice

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

# After a command, skip polls for this many seconds to avoid
# the device returning stale data that overwrites optimistic state.
COMMAND_DEBOUNCE_SECONDS = 5


class SkyLiteEvolveCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching data from the projector."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: TuyaCloudApi | TuyaLocalDevice,
        device_id: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Sky Lite Evolve",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self.device_id = device_id
        self._last_command_time: float = 0

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the projector."""
        # Skip poll if a command was sent recently (local only)
        if (
            isinstance(self.api, TuyaLocalDevice)
            and self.data
            and (time.monotonic() - self._last_command_time) < COMMAND_DEBOUNCE_SECONDS
        ):
            _LOGGER.debug("Skipping poll during command debounce window")
            return self.data

        try:
            return await self.api.get_device_status()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def async_send_command(self, dps_key: str, value: Any) -> None:
        """Send a single command and optimistically update local state."""
        await self.api.send_command(dps_key, value)
        self._last_command_time = time.monotonic()
        if self.data is not None:
            self.data[dps_key] = value
            self.async_set_updated_data(self.data)

    async def async_send_commands(self, commands: dict[str, Any]) -> None:
        """Send multiple commands and optimistically update local state."""
        await self.api.send_commands(commands)
        self._last_command_time = time.monotonic()
        if self.data is not None:
            self.data.update(commands)
            self.async_set_updated_data(self.data)
