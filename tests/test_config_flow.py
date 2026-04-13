"""Tests for the Sky Lite Evolve config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.sky_lite_evolve.const import (
    CONF_ACCESS_KEY,
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_REGION,
    CONF_SECRET_KEY,
    CONNECTION_TYPE_CLOUD,
    CONNECTION_TYPE_LOCAL,
    DOMAIN,
)
from custom_components.sky_lite_evolve.tuya_api import CannotConnect, InvalidAuth


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    """Test the initial user step shows connection type selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_user_step_cloud_selected(hass: HomeAssistant) -> None:
    """Test selecting cloud connection type goes to cloud step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud"


async def test_user_step_local_selected(hass: HomeAssistant) -> None:
    """Test selecting local connection type goes to local step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "local"


async def test_cloud_step_success(
    hass: HomeAssistant, mock_tuya_cloud_api: AsyncMock
) -> None:
    """Test successful cloud configuration creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ACCESS_KEY: "test_access_key",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_DEVICE_ID: "test_device_id",
            CONF_REGION: "us",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Sky Lite Evolve"
    assert result["data"][CONF_CONNECTION_TYPE] == CONNECTION_TYPE_CLOUD
    assert result["data"][CONF_DEVICE_ID] == "test_device_id"


async def test_cloud_step_invalid_auth(hass: HomeAssistant) -> None:
    """Test cloud config flow handles auth errors."""
    with patch(
        "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
    ) as mock_cls:
        mock_cls.return_value.get_device_info = AsyncMock(side_effect=InvalidAuth)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCESS_KEY: "bad_key",
                CONF_SECRET_KEY: "bad_secret",
                CONF_DEVICE_ID: "test_device_id",
                CONF_REGION: "us",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_cloud_step_cannot_connect(hass: HomeAssistant) -> None:
    """Test cloud config flow handles connection errors."""
    with patch(
        "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
    ) as mock_cls:
        mock_cls.return_value.get_device_info = AsyncMock(side_effect=CannotConnect)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCESS_KEY: "test_key",
                CONF_SECRET_KEY: "test_secret",
                CONF_DEVICE_ID: "test_device_id",
                CONF_REGION: "us",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_local_step_success(
    hass: HomeAssistant, mock_tuya_local_device: AsyncMock
) -> None:
    """Test successful local configuration creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ACCESS_KEY: "test_access_key",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_DEVICE_ID: "test_device_id",
            CONF_REGION: "us",
            CONF_IP_ADDRESS: "192.168.1.100",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Sky Lite Evolve"
    assert result["data"][CONF_CONNECTION_TYPE] == CONNECTION_TYPE_LOCAL


async def test_local_step_cannot_connect(hass: HomeAssistant) -> None:
    """Test local config flow handles connection errors."""
    with (
        patch(
            "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
        ) as mock_cloud_cls,
        patch(
            "custom_components.sky_lite_evolve.config_flow.TuyaLocalDevice",
        ) as mock_local_cls,
    ):
        mock_cloud_cls.return_value.get_device_info = AsyncMock(
            return_value={"name": "Sky Lite Evolve", "local_key": "test_local_key"}
        )
        mock_local_cls.return_value.get_device_status = AsyncMock(
            side_effect=CannotConnect
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCESS_KEY: "test_access_key",
                CONF_SECRET_KEY: "test_secret_key",
                CONF_DEVICE_ID: "test_device_id",
                CONF_REGION: "us",
                CONF_IP_ADDRESS: "192.168.1.100",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_cloud_step_unknown_error(hass: HomeAssistant) -> None:
    """Test cloud config flow handles unexpected errors."""
    with patch(
        "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
    ) as mock_cls:
        mock_cls.return_value.get_device_info = AsyncMock(
            side_effect=RuntimeError("boom")
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCESS_KEY: "test_key",
                CONF_SECRET_KEY: "test_secret",
                CONF_DEVICE_ID: "test_device_id",
                CONF_REGION: "us",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_local_step_invalid_auth(hass: HomeAssistant) -> None:
    """Test local config flow handles auth errors from cloud key fetch."""
    with patch(
        "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
    ) as mock_cloud_cls:
        mock_cloud_cls.return_value.get_device_info = AsyncMock(side_effect=InvalidAuth)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCESS_KEY: "bad_key",
                CONF_SECRET_KEY: "bad_secret",
                CONF_DEVICE_ID: "test_device_id",
                CONF_REGION: "us",
                CONF_IP_ADDRESS: "192.168.1.100",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_local_step_unknown_error(hass: HomeAssistant) -> None:
    """Test local config flow handles unexpected errors."""
    with patch(
        "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
    ) as mock_cloud_cls:
        mock_cloud_cls.return_value.get_device_info = AsyncMock(
            side_effect=RuntimeError("boom")
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCESS_KEY: "test_key",
                CONF_SECRET_KEY: "test_secret",
                CONF_DEVICE_ID: "test_device_id",
                CONF_REGION: "us",
                CONF_IP_ADDRESS: "192.168.1.100",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_local_step_no_local_key(hass: HomeAssistant) -> None:
    """Test local flow errors when cloud API returns no local_key."""
    with patch(
        "custom_components.sky_lite_evolve.config_flow.TuyaCloudApi",
    ) as mock_cloud_cls:
        mock_cloud_cls.return_value.get_device_info = AsyncMock(
            return_value={"name": "Sky Lite Evolve"}
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCESS_KEY: "test_key",
                CONF_SECRET_KEY: "test_secret",
                CONF_DEVICE_ID: "test_device_id",
                CONF_REGION: "us",
                CONF_IP_ADDRESS: "192.168.1.100",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_cloud_duplicate_device(
    hass: HomeAssistant, mock_tuya_cloud_api: AsyncMock, mock_cloud_config_entry
) -> None:
    """Test that configuring a device that already exists is aborted."""
    mock_cloud_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ACCESS_KEY: "test_access_key",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_DEVICE_ID: "test_device_id",
            CONF_REGION: "us",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
