"""Tests for Sky Lite Evolve integration setup and unload."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sky_lite_evolve.const import (
    CONF_ACCESS_KEY,
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_LOCAL_KEY,
    CONF_REGION,
    CONF_SECRET_KEY,
    CONNECTION_TYPE_CLOUD,
    CONNECTION_TYPE_LOCAL,
    DOMAIN,
)

MOCK_STATUS = {
    "20": True,
    "24": "000003e803e8",
    "51": "colour",
    "52": True,
    "53": True,
    "54": 500,
    "60": True,
    "62": 50,
}


def _mock_cloud_api():
    api = MagicMock()
    api.get_device_specification = AsyncMock(return_value={"functions": []})
    api.get_device_status = AsyncMock(return_value=MOCK_STATUS)
    api.close = AsyncMock()
    api.send_command = AsyncMock()
    api.send_commands = AsyncMock()
    return api


def _mock_local_api():
    api = MagicMock()
    api.get_device_status = AsyncMock(return_value=MOCK_STATUS)
    api.close = AsyncMock()
    api.send_command = AsyncMock()
    api.send_commands = AsyncMock()
    return api


async def test_setup_cloud_entry(hass: HomeAssistant) -> None:
    """Test setting up a cloud config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD,
            CONF_ACCESS_KEY: "test_access_key",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_DEVICE_ID: "test_device_id",
            CONF_REGION: "us",
        },
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    mock_api = _mock_cloud_api()

    with patch(
        "custom_components.sky_lite_evolve.create_api_client",
        return_value=mock_api,
    ):
        # isinstance check for TuyaCloudApi — also patch that
        with patch(
            "custom_components.sky_lite_evolve.TuyaCloudApi",
        ) as mock_cloud_cls:
            mock_cloud_cls.return_value = mock_api
            # Make isinstance work
            with patch(
                "custom_components.sky_lite_evolve.isinstance",
                side_effect=lambda obj, cls: obj is mock_api,
            ):
                pass
        # Simpler approach: just patch create_api_client
        with (
            patch(
                "custom_components.sky_lite_evolve.create_api_client",
                return_value=mock_api,
            ),
            patch(
                "custom_components.sky_lite_evolve.isinstance",
                create=True,
            ),
        ):
            pass

    # Actually, the simplest approach: make mock_api an instance of TuyaCloudApi
    # by using spec. But spec won't pass isinstance. Let me re-think.
    # The code does: isinstance(api, TuyaCloudApi)
    # We need to either:
    # 1. Return a real TuyaCloudApi (too complex)
    # 2. Patch isinstance (fragile)
    # 3. Just patch the whole function and test both paths

    # Test cloud path (isinstance returns True because we patch create_api_client
    # to return an object, and also patch the isinstance check)
    mock_api = _mock_cloud_api()

    with patch(
        "custom_components.sky_lite_evolve.create_api_client",
        return_value=mock_api,
    ):
        from custom_components.sky_lite_evolve.tuya_api import TuyaCloudApi

        mock_api.__class__ = TuyaCloudApi

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state.name == "LOADED"
    mock_api.get_device_specification.assert_called_once()


async def test_setup_cloud_entry_spec_fails(hass: HomeAssistant) -> None:
    """Test setup continues when device spec fetch fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD,
            CONF_ACCESS_KEY: "test_access_key",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_DEVICE_ID: "test_device_id",
            CONF_REGION: "us",
        },
        unique_id="test_device_id_spec_fail",
    )
    entry.add_to_hass(hass)

    mock_api = _mock_cloud_api()
    mock_api.get_device_specification = AsyncMock(side_effect=OSError("timeout"))

    from custom_components.sky_lite_evolve.tuya_api import TuyaCloudApi

    mock_api.__class__ = TuyaCloudApi

    with patch(
        "custom_components.sky_lite_evolve.create_api_client",
        return_value=mock_api,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state.name == "LOADED"


async def test_setup_local_entry(hass: HomeAssistant) -> None:
    """Test setting up a local config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL,
            CONF_DEVICE_ID: "test_device_id",
            CONF_LOCAL_KEY: "test_local_key",
            CONF_IP_ADDRESS: "192.168.1.100",
        },
        unique_id="test_device_id_local",
    )
    entry.add_to_hass(hass)

    mock_api = _mock_local_api()

    with patch(
        "custom_components.sky_lite_evolve.create_api_client",
        return_value=mock_api,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state.name == "LOADED"


async def test_unload_entry(hass: HomeAssistant) -> None:
    """Test unloading a config entry calls close."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL,
            CONF_DEVICE_ID: "test_device_id",
            CONF_LOCAL_KEY: "test_local_key",
            CONF_IP_ADDRESS: "192.168.1.100",
        },
        unique_id="test_device_id_unload",
    )
    entry.add_to_hass(hass)

    mock_api = _mock_local_api()

    with patch(
        "custom_components.sky_lite_evolve.create_api_client",
        return_value=mock_api,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.async_unload(entry.entry_id)

    assert result is True
    mock_api.close.assert_called_once()
