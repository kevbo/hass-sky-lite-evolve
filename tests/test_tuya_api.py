"""Tests for the Tuya API module."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sky_lite_evolve.tuya_api import (
    CLOUD_CODE_TO_DPS,
    DPS_TO_CLOUD,
    CannotConnect,
    CannotConnectError,
    InvalidAuth,
    InvalidAuthError,
    TuyaCloudApi,
    TuyaLocalDevice,
    create_api_client,
)

# ---------------------------------------------------------------------------
# Exception aliases
# ---------------------------------------------------------------------------


def test_exception_aliases() -> None:
    assert CannotConnect is CannotConnectError
    assert InvalidAuth is InvalidAuthError


# ---------------------------------------------------------------------------
# Mapping consistency
# ---------------------------------------------------------------------------


def test_dps_to_cloud_is_inverse_of_cloud_to_dps() -> None:
    for cloud_code, dps_key in CLOUD_CODE_TO_DPS.items():
        assert DPS_TO_CLOUD[dps_key] == cloud_code


# ---------------------------------------------------------------------------
# create_api_client
# ---------------------------------------------------------------------------


def test_create_api_client_cloud(hass: HomeAssistant) -> None:
    config = {
        "connection_type": "cloud",
        "access_key": "ak",
        "secret_key": "sk",
        "device_id": "did",
        "region": "us",
    }
    client = create_api_client(hass, config)
    assert isinstance(client, TuyaCloudApi)


def test_create_api_client_local(hass: HomeAssistant) -> None:
    config = {
        "connection_type": "local",
        "device_id": "did",
        "local_key": "lk",
        "ip_address": "192.168.1.1",
    }
    client = create_api_client(hass, config)
    assert isinstance(client, TuyaLocalDevice)


# ---------------------------------------------------------------------------
# TuyaLocalDevice._encode_value
# ---------------------------------------------------------------------------


class TestEncodeValue:
    """Tests for TuyaLocalDevice._encode_value."""

    def test_hsv_dict(self) -> None:
        result = TuyaLocalDevice._encode_value({"h": 180, "s": 500, "v": 200})
        assert result == "00b401f400c8"

    def test_hsv_dict_zero(self) -> None:
        result = TuyaLocalDevice._encode_value({"h": 0, "s": 0, "v": 0})
        assert result == "000000000000"

    def test_regular_dict(self) -> None:
        result = TuyaLocalDevice._encode_value({"foo": "bar"})
        assert result == '{"foo":"bar"}'

    def test_list(self) -> None:
        result = TuyaLocalDevice._encode_value([1, 2, 3])
        assert result == "[1,2,3]"

    def test_plain_value(self) -> None:
        assert TuyaLocalDevice._encode_value(True) is True
        assert TuyaLocalDevice._encode_value(42) == 42
        assert TuyaLocalDevice._encode_value("hello") == "hello"


# ---------------------------------------------------------------------------
# TuyaLocalDevice.get_device_info
# ---------------------------------------------------------------------------


async def test_local_get_device_info(hass: HomeAssistant) -> None:
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    info = await device.get_device_info()
    assert info == {"id": "dev123", "name": "Sky Lite Evolve"}


# ---------------------------------------------------------------------------
# TuyaLocalDevice.get_device_status
# ---------------------------------------------------------------------------


async def test_local_get_device_status_success(hass: HomeAssistant) -> None:
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    mock_dev = MagicMock()
    mock_dev.status.return_value = {"dps": {"20": True, "51": "colour"}}
    device._device = mock_dev

    with patch.object(
        hass, "async_add_executor_job", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = {"dps": {"20": True, "51": "colour"}}
        result = await device.get_device_status()

    assert result == {"20": True, "51": "colour"}


async def test_local_get_device_status_retry(hass: HomeAssistant) -> None:
    """Test that get_device_status retries on empty DPS."""
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    call_count = 0

    async def fake_exec(func, *args):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return {"dps": {}}
        return {"dps": {"20": True}}

    with patch.object(hass, "async_add_executor_job", side_effect=fake_exec):
        result = await device.get_device_status()

    assert result == {"20": True}
    assert call_count == 3


async def test_local_get_device_status_exception(hass: HomeAssistant) -> None:
    """Test CannotConnect raised on exception from tinytuya."""
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    with (
        patch.object(
            hass,
            "async_add_executor_job",
            new_callable=AsyncMock,
            side_effect=OSError("connection refused"),
        ),
        pytest.raises(CannotConnect, match="Local status failed"),
    ):
        await device.get_device_status()

    assert device._device is None  # reset after error


async def test_local_get_device_status_all_retries_exhausted(
    hass: HomeAssistant,
) -> None:
    """Test CannotConnect when all retries return empty DPS."""
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    async def fake_exec(func, *args):
        return {"dps": {}}

    with (
        patch.object(hass, "async_add_executor_job", side_effect=fake_exec),
        pytest.raises(CannotConnect, match="Local status error"),
    ):
        await device.get_device_status()


async def test_local_get_device_status_error_dict(hass: HomeAssistant) -> None:
    """Test CannotConnect with error dict from tinytuya."""
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    async def fake_exec(func, *args):
        return {"Error": "Network timeout", "Err": "905"}

    with (
        patch.object(hass, "async_add_executor_job", side_effect=fake_exec),
        pytest.raises(CannotConnect, match="Network timeout"),
    ):
        await device.get_device_status()


# ---------------------------------------------------------------------------
# TuyaLocalDevice.send_command
# ---------------------------------------------------------------------------


async def test_local_send_command_success(hass: HomeAssistant) -> None:
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    with patch.object(
        hass, "async_add_executor_job", new_callable=AsyncMock, return_value=None
    ):
        result = await device.send_command("20", True)

    assert result is True


async def test_local_send_command_error(hass: HomeAssistant) -> None:
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    with (
        patch.object(
            hass,
            "async_add_executor_job",
            new_callable=AsyncMock,
            side_effect=OSError("send failed"),
        ),
        pytest.raises(CannotConnect, match="Local send failed"),
    ):
        await device.send_command("20", True)

    assert device._device is None


# ---------------------------------------------------------------------------
# TuyaLocalDevice.send_commands
# ---------------------------------------------------------------------------


async def test_local_send_commands_success(hass: HomeAssistant) -> None:
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    with patch.object(
        hass, "async_add_executor_job", new_callable=AsyncMock, return_value=None
    ):
        result = await device.send_commands({"20": True, "52": True})

    assert result is True


async def test_local_send_commands_encodes_hsv(hass: HomeAssistant) -> None:
    """Test that HSV dicts are encoded as hex for local commands."""
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    with patch.object(
        hass, "async_add_executor_job", new_callable=AsyncMock, return_value=None
    ) as mock_exec:
        await device.send_commands({"24": {"h": 180, "s": 500, "v": 200}})

    # Check that set_multiple_values was called with encoded hex
    call_args = mock_exec.call_args
    encoded_arg = call_args[0][1]
    assert encoded_arg["24"] == "00b401f400c8"


async def test_local_send_commands_error(hass: HomeAssistant) -> None:
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()

    with (
        patch.object(
            hass,
            "async_add_executor_job",
            new_callable=AsyncMock,
            side_effect=OSError("send failed"),
        ),
        pytest.raises(CannotConnect, match="Local send failed"),
    ):
        await device.send_commands({"20": True})


# ---------------------------------------------------------------------------
# TuyaLocalDevice.close
# ---------------------------------------------------------------------------


async def test_local_close(hass: HomeAssistant) -> None:
    device = TuyaLocalDevice(hass, "dev123", "key", "192.168.1.1")
    device._device = MagicMock()
    await device.close()
    assert device._device is None


# ---------------------------------------------------------------------------
# TuyaCloudApi (backed by tinytuya.Cloud)
# ---------------------------------------------------------------------------


class TestTuyaCloudApi:
    """Tests for TuyaCloudApi wrapping tinytuya.Cloud."""

    def _create(self, hass: HomeAssistant):
        api = TuyaCloudApi(
            hass=hass,
            access_key="ak",
            secret_key="sk",
            device_id="did",
            region="us",
        )
        mock_cloud = MagicMock()
        api._cloud = mock_cloud
        return api, mock_cloud

    async def test_get_device_info(self, hass: HomeAssistant) -> None:
        api, mock_cloud = self._create(hass)
        mock_cloud.cloudrequest.return_value = {
            "success": True,
            "result": {"name": "Sky Lite Evolve", "id": "did"},
        }
        with patch.object(
            hass,
            "async_add_executor_job",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "result": {"name": "Sky Lite Evolve", "id": "did"},
            },
        ):
            info = await api.get_device_info()
        assert info["name"] == "Sky Lite Evolve"

    async def test_get_device_info_invalid_auth(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        with (
            patch.object(
                hass,
                "async_add_executor_job",
                new_callable=AsyncMock,
                return_value={"success": False, "msg": "Invalid sign token"},
            ),
            pytest.raises(InvalidAuth),
        ):
            await api.get_device_info()

    async def test_get_device_info_cannot_connect(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        with (
            patch.object(
                hass,
                "async_add_executor_job",
                new_callable=AsyncMock,
                return_value={"success": False, "msg": "Service unavailable"},
            ),
            pytest.raises(CannotConnect),
        ):
            await api.get_device_info()

    async def test_check_response_unexpected(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        with (
            patch.object(
                hass,
                "async_add_executor_job",
                new_callable=AsyncMock,
                return_value=None,
            ),
            pytest.raises(CannotConnect, match="unexpected response"),
        ):
            await api.get_device_info()

    async def test_get_device_status(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        with patch.object(
            hass,
            "async_add_executor_job",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "result": [
                    {"code": "switch_led", "value": True},
                    {"code": "colour_data", "value": "000003e803e8"},
                    {"code": "star_work_mode", "value": "colour"},
                    {"code": "unknown_code", "value": 42},
                ],
            },
        ):
            result = await api.get_device_status()
        assert result["20"] is True
        assert result["24"] == "000003e803e8"
        assert result["51"] == "colour"
        assert "unknown_code" not in result

    async def test_get_device_specification(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        with patch.object(
            hass,
            "async_add_executor_job",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "result": {"functions": [], "status": []},
            },
        ):
            spec = await api.get_device_specification()
        assert "functions" in spec

    async def test_send_command_success(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        with patch.object(
            hass,
            "async_add_executor_job",
            new_callable=AsyncMock,
            return_value={"success": True, "result": True},
        ):
            result = await api.send_command("20", True)
        assert result is True

    async def test_send_command_unknown_dps(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        result = await api.send_command("999", True)
        assert result is False

    async def test_send_command_api_error(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        with (
            patch.object(
                hass,
                "async_add_executor_job",
                new_callable=AsyncMock,
                return_value={"success": False, "msg": "Device offline"},
            ),
            pytest.raises(CannotConnect, match="Device offline"),
        ):
            await api.send_command("20", True)

    async def test_send_commands_success(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        with patch.object(
            hass,
            "async_add_executor_job",
            new_callable=AsyncMock,
            return_value={"success": True, "result": True},
        ):
            result = await api.send_commands({"20": True, "52": True})
        assert result is True

    async def test_send_commands_all_unknown(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        result = await api.send_commands({"999": True})
        assert result is False

    async def test_close_is_noop(self, hass: HomeAssistant) -> None:
        api, _ = self._create(hass)
        await api.close()  # should not raise

    async def test_get_cloud_lazy_init(self, hass: HomeAssistant) -> None:
        """Test that _get_cloud lazily creates a tinytuya.Cloud instance."""
        api = TuyaCloudApi(
            hass=hass,
            access_key="ak",
            secret_key="sk",
            device_id="did",
            region="us",
        )
        assert api._cloud is None
        with patch.dict("sys.modules", {"tinytuya": MagicMock()}):
            mock_tt = sys.modules["tinytuya"]
            cloud = api._get_cloud()
            mock_tt.Cloud.assert_called_once_with(
                apiRegion="us",
                apiKey="ak",
                apiSecret="sk",
                apiDeviceID="did",
                initial_token="deferred",
            )
            assert cloud is mock_tt.Cloud.return_value
