"""Tests for the Sky Lite Evolve coordinator."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.sky_lite_evolve.coordinator import (
    COMMAND_DEBOUNCE_SECONDS,
    SkyLiteEvolveCoordinator,
)
from custom_components.sky_lite_evolve.tuya_api import TuyaLocalDevice


@pytest.fixture
def mock_api():
    api = MagicMock()
    api.get_device_status = AsyncMock(
        return_value={"20": True, "24": "000003e803e8", "51": "colour"}
    )
    api.send_command = AsyncMock()
    api.send_commands = AsyncMock()
    api.close = AsyncMock()
    return api


async def test_update_data(hass: HomeAssistant, mock_api: MagicMock) -> None:
    coord = SkyLiteEvolveCoordinator(hass, mock_api, "test_device_id")
    data = await coord._async_update_data()
    assert data == {"20": True, "24": "000003e803e8", "51": "colour"}
    mock_api.get_device_status.assert_called_once()


async def test_update_data_error(hass: HomeAssistant, mock_api: MagicMock) -> None:
    mock_api.get_device_status = AsyncMock(side_effect=Exception("device offline"))
    coord = SkyLiteEvolveCoordinator(hass, mock_api, "test_device_id")
    with pytest.raises(UpdateFailed, match="Error fetching data"):
        await coord._async_update_data()


async def test_send_command(hass: HomeAssistant, mock_api: MagicMock) -> None:
    coord = SkyLiteEvolveCoordinator(hass, mock_api, "test_device_id")
    coord.data = {"20": False}
    coord.async_set_updated_data = MagicMock()
    await coord.async_send_command("20", True)
    mock_api.send_command.assert_called_once_with("20", True)
    assert coord.data["20"] is True
    coord.async_set_updated_data.assert_called_once()


async def test_send_command_no_data(hass: HomeAssistant, mock_api: MagicMock) -> None:
    coord = SkyLiteEvolveCoordinator(hass, mock_api, "test_device_id")
    coord.data = None
    await coord.async_send_command("20", True)
    mock_api.send_command.assert_called_once_with("20", True)


async def test_send_commands(hass: HomeAssistant, mock_api: MagicMock) -> None:
    coord = SkyLiteEvolveCoordinator(hass, mock_api, "test_device_id")
    coord.data = {"20": False, "52": False}
    coord.async_set_updated_data = MagicMock()
    await coord.async_send_commands({"20": True, "52": True})
    mock_api.send_commands.assert_called_once_with({"20": True, "52": True})
    assert coord.data["20"] is True
    assert coord.data["52"] is True


async def test_send_commands_no_data(hass: HomeAssistant, mock_api: MagicMock) -> None:
    coord = SkyLiteEvolveCoordinator(hass, mock_api, "test_device_id")
    coord.data = None
    await coord.async_send_commands({"20": True})
    mock_api.send_commands.assert_called_once()


async def test_debounce_skips_poll(hass: HomeAssistant) -> None:
    """Test that poll is skipped during debounce window for local devices."""
    mock_local = MagicMock(spec=TuyaLocalDevice)
    mock_local.get_device_status = AsyncMock()
    mock_local.send_command = AsyncMock()

    coord = SkyLiteEvolveCoordinator(hass, mock_local, "test_device_id")
    coord.data = {"20": True}
    coord.async_set_updated_data = MagicMock()

    # Simulate a recent command
    coord._last_command_time = time.monotonic()

    result = await coord._async_update_data()
    assert result == {"20": True}
    mock_local.get_device_status.assert_not_called()


async def test_debounce_expired_polls(hass: HomeAssistant) -> None:
    """Test that poll happens after debounce window expires."""
    mock_local = MagicMock(spec=TuyaLocalDevice)
    mock_local.get_device_status = AsyncMock(return_value={"20": False})

    coord = SkyLiteEvolveCoordinator(hass, mock_local, "test_device_id")
    coord.data = {"20": True}

    coord._last_command_time = time.monotonic() - COMMAND_DEBOUNCE_SECONDS - 1

    result = await coord._async_update_data()
    assert result == {"20": False}
    mock_local.get_device_status.assert_called_once()
