"""Fixtures for Sky Lite Evolve tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    return


@pytest.fixture
def mock_cloud_config_entry() -> MockConfigEntry:
    """Create a mock cloud config entry."""
    return MockConfigEntry(
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


@pytest.fixture
def mock_local_config_entry() -> MockConfigEntry:
    """Create a mock local config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL,
            CONF_DEVICE_ID: "test_device_id",
            CONF_LOCAL_KEY: "test_local_key",
            CONF_IP_ADDRESS: "192.168.1.100",
        },
        unique_id="test_device_id",
    )


@pytest.fixture
def mock_tuya_cloud_api():
    """Mock TuyaCloudApi for config flow and setup."""
    mock_api = MagicMock()
    mock_api.get_device_info = AsyncMock(return_value={"name": "Sky Lite Evolve"})
    mock_api.get_device_specification = AsyncMock(return_value={"functions": []})
    mock_api.get_device_status = AsyncMock(
        return_value={
            "20": True,
            "24": "000003e803e8",
            "51": "colour",
            "52": True,
            "53": True,
            "54": 500,
            "62": 50,
        }
    )
    mock_api.send_command = AsyncMock()
    mock_api.send_commands = AsyncMock()
    mock_api.close = AsyncMock()

    with (
        patch(
            "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
            return_value=mock_api,
        ),
        patch(
            "custom_components.sky_lite_evolve.create_api_client",
            return_value=mock_api,
        ),
    ):
        yield mock_api


@pytest.fixture
def mock_tuya_local_device():
    """Mock TuyaCloudApi (for local key fetch) and TuyaLocalDevice."""
    mock_local = MagicMock()
    mock_local.get_device_status = AsyncMock(
        return_value={
            "20": True,
            "24": "000003e803e8",
            "51": "colour",
            "52": True,
            "53": True,
            "54": 500,
            "62": 50,
        }
    )
    mock_local.send_command = AsyncMock()
    mock_local.send_commands = AsyncMock()
    mock_local.close = AsyncMock()

    with (
        patch(
            "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
        ) as mock_cloud_cls,
        patch(
            "custom_components.sky_lite_evolve.config_flow.TuyaLocalDevice",
            return_value=mock_local,
        ),
        patch(
            "custom_components.sky_lite_evolve.create_api_client",
            return_value=mock_local,
        ),
    ):
        cloud_instance = mock_cloud_cls.return_value
        cloud_instance.get_device_info = AsyncMock(
            return_value={"name": "Sky Lite Evolve", "local_key": "test_local_key"}
        )

        yield mock_local
