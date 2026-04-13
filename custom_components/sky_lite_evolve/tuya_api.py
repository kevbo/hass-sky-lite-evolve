"""Tuya API client supporting both cloud and local connections."""

from __future__ import annotations

import contextlib
import json
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CMD_BRIGHTNESS,
    CMD_COLOR,
    CMD_COLOR_STATE,
    CMD_LASER_BRIGHTNESS,
    CMD_LASER_STATE,
    CMD_MODE,
    CMD_MOTOR_STATE,
    CMD_ROTATION,
    CMD_SCENE,
    CMD_SWITCH_LED,
    CONNECTION_TYPE_LOCAL,
    DPS_BRIGHTNESS,
    DPS_COLOR,
    DPS_COLOR_STATE,
    DPS_LASER_BRIGHTNESS,
    DPS_LASER_STATE,
    DPS_MODE,
    DPS_MOTOR_STATE,
    DPS_POWER,
    DPS_ROTATION,
    DPS_SCENE,
    TUYA_VERSION,
)

_LOGGER = logging.getLogger(__name__)

# Cloud command code -> DPS mapping (for normalizing cloud responses)
CLOUD_CODE_TO_DPS = {
    CMD_SWITCH_LED: DPS_POWER,
    CMD_MODE: DPS_MODE,
    CMD_COLOR_STATE: DPS_COLOR_STATE,
    CMD_LASER_STATE: DPS_LASER_STATE,
    CMD_LASER_BRIGHTNESS: DPS_LASER_BRIGHTNESS,
    CMD_BRIGHTNESS: DPS_BRIGHTNESS,
    CMD_COLOR: DPS_COLOR,
    CMD_SCENE: DPS_SCENE,
    CMD_MOTOR_STATE: DPS_MOTOR_STATE,
    CMD_ROTATION: DPS_ROTATION,
}

# DPS -> cloud command code (for sending commands)
DPS_TO_CLOUD = {v: k for k, v in CLOUD_CODE_TO_DPS.items()}


class CannotConnectError(Exception):
    """Error to indicate we cannot connect."""


# Backward-compatible alias
CannotConnect = CannotConnectError


class InvalidAuthError(Exception):
    """Error to indicate invalid authentication."""


# Backward-compatible alias
InvalidAuth = InvalidAuthError


class TuyaCloudApi:
    """Tuya Cloud API client using tinytuya.Cloud."""

    def __init__(
        self,
        hass: HomeAssistant,
        access_key: str,
        secret_key: str,
        device_id: str,
        region: str,
    ) -> None:
        self._hass = hass
        self._device_id = device_id
        self._cloud = None
        self._access_key = access_key
        self._secret_key = secret_key
        self._region = region

    def _get_cloud(self):  # noqa: ANN202
        if self._cloud is None:
            import tinytuya  # noqa: PLC0415

            self._cloud = tinytuya.Cloud(
                apiRegion=self._region,
                apiKey=self._access_key,
                apiSecret=self._secret_key,
                apiDeviceID=self._device_id,
                initial_token="deferred",  # noqa: S106
            )
        return self._cloud

    @staticmethod
    def _check_response(data: dict[str, Any], context: str) -> None:
        """Check a tinytuya.Cloud response and raise on errors."""
        if not isinstance(data, dict):
            raise CannotConnect(f"{context}: unexpected response")
        if data.get("success"):
            return
        msg = data.get("msg", "Unknown error")
        if "sign" in msg.lower() or "invalid" in msg.lower():
            raise InvalidAuth(f"{context}: {msg}")
        raise CannotConnect(f"{context}: {msg}")

    async def get_device_info(self) -> dict[str, Any]:
        """Get device information via /v1.0/devices/{id}."""
        cloud = self._get_cloud()
        data = await self._hass.async_add_executor_job(
            cloud.cloudrequest, f"/v1.0/devices/{self._device_id}"
        )
        self._check_response(data, "get_device_info")
        return data["result"]

    async def get_device_status(self) -> dict[str, Any]:
        """Get device status as a DPS-keyed dict."""
        cloud = self._get_cloud()
        data = await self._hass.async_add_executor_job(cloud.getstatus, self._device_id)
        self._check_response(data, "get_device_status")
        result: dict[str, Any] = {}
        for item in data.get("result", []):
            code = item.get("code", "")
            value = item.get("value")
            _LOGGER.debug("Status item: code=%s, value=%s", code, value)
            dps_key = CLOUD_CODE_TO_DPS.get(code)
            if dps_key is not None:
                result[dps_key] = value
        return result

    async def get_device_specification(self) -> dict[str, Any]:
        """Get device specification (supported functions and their value ranges)."""
        cloud = self._get_cloud()
        data = await self._hass.async_add_executor_job(
            cloud.cloudrequest,
            f"/v1.0/iot-03/devices/{self._device_id}/specification",
        )
        self._check_response(data, "get_device_specification")
        return data.get("result", {})

    async def send_command(self, dps_key: str, value: Any) -> bool:
        """Send a command using the cloud command code."""
        cloud_code = DPS_TO_CLOUD.get(dps_key)
        if cloud_code is None:
            _LOGGER.error("Unknown DPS key: %s", dps_key)
            return False

        commands = {"commands": [{"code": cloud_code, "value": value}]}
        _LOGGER.debug("Sending command: %s", commands)
        cloud = self._get_cloud()
        data = await self._hass.async_add_executor_job(
            cloud.sendcommand, self._device_id, commands
        )
        self._check_response(data, "send_command")
        return data.get("result", False)

    async def send_commands(self, commands: dict[str, Any]) -> bool:
        """Send multiple commands at once."""
        cmd_list = []
        for dps_key, value in commands.items():
            cloud_code = DPS_TO_CLOUD.get(dps_key)
            if cloud_code is None:
                _LOGGER.error("Unknown DPS key: %s", dps_key)
                continue
            cmd_list.append({"code": cloud_code, "value": value})

        if not cmd_list:
            return False

        body = {"commands": cmd_list}
        _LOGGER.debug("Sending commands: %s", body)
        cloud = self._get_cloud()
        data = await self._hass.async_add_executor_job(
            cloud.sendcommand, self._device_id, body
        )
        self._check_response(data, "send_commands")
        return data.get("result", False)

    async def close(self) -> None:
        """No-op: tinytuya.Cloud manages its own sessions."""


class TuyaLocalDevice:
    """Local Tuya device using tinytuya."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_id: str,
        local_key: str,
        ip_address: str,
    ) -> None:
        self._hass = hass
        self._device_id = device_id
        self._local_key = local_key
        self._ip_address = ip_address
        self._device = None

    def _get_device(self):  # noqa: ANN202
        if self._device is None:
            import tinytuya  # noqa: PLC0415  # lazy import: only needed for local mode

            self._device = tinytuya.Device(
                self._device_id,
                self._ip_address,
                self._local_key,
                version=float(TUYA_VERSION),
            )
            self._device.set_socketPersistent(True)
            self._device.set_socketRetryLimit(2)
            self._device.set_socketTimeout(5)
        return self._device

    def _reset_device(self) -> None:
        """Close and reset the device connection."""
        if self._device:
            with contextlib.suppress(OSError):
                self._device.close()
            self._device = None

    @staticmethod
    def _encode_value(value: Any) -> Any:
        """
        Encode values for the local protocol.

        Colour data dicts (h/s/v) are encoded as hex: HHHHSSSSVVVV.
        Other dicts/lists are JSON-encoded.
        """
        if isinstance(value, dict) and "h" in value and "s" in value and "v" in value:
            return f"{value['h']:04x}{value['s']:04x}{value['v']:04x}"
        if isinstance(value, (dict, list)):
            return json.dumps(value, separators=(",", ":"))
        return value

    async def get_device_info(self) -> dict[str, Any]:
        """Get basic device info (limited in local mode)."""
        return {"id": self._device_id, "name": "Sky Lite Evolve"}

    async def get_device_status(self) -> dict[str, Any]:
        """
        Get device status as a DPS-keyed dict.

        With persistent sockets, the first status() call may return a stale
        ack or partial response. Retry up to 3 times to get a valid DPS dict.
        """
        device = self._get_device()
        last_err = None
        for attempt in range(3):
            try:
                data = await self._hass.async_add_executor_job(device.status)
            except Exception as err:
                self._reset_device()
                raise CannotConnect(f"Local status failed: {err}") from err

            _LOGGER.debug("Local device status (attempt %d): %s", attempt + 1, data)

            if isinstance(data, dict) and "dps" in data and data["dps"]:
                return data["dps"]

            last_err = data

        # All retries exhausted
        err_msg = (
            last_err.get("Error", "No DPS in response")
            if isinstance(last_err, dict)
            else str(last_err)
        )
        self._reset_device()
        raise CannotConnect(f"Local status error: {err_msg}")

    async def send_command(self, dps_key: str, value: Any) -> bool:
        """Set a single DPS value. Returns the response data if available."""
        device = self._get_device()
        encoded = self._encode_value(value)
        try:
            data = await self._hass.async_add_executor_job(
                device.set_value, dps_key, encoded
            )
        except Exception as err:
            self._reset_device()
            raise CannotConnect(f"Local send failed: {err}") from err
        _LOGGER.debug("Local set_value response: %s", data)
        return True

    async def send_commands(self, commands: dict[str, Any]) -> bool:
        """Set multiple DPS values."""
        device = self._get_device()
        encoded = {k: self._encode_value(v) for k, v in commands.items()}
        try:
            data = await self._hass.async_add_executor_job(
                device.set_multiple_values, encoded
            )
        except Exception as err:
            self._reset_device()
            raise CannotConnect(f"Local send failed: {err}") from err
        _LOGGER.debug("Local set_multiple_values response: %s", data)
        return True

    async def close(self) -> None:
        """Close connection."""
        self._reset_device()


def create_api_client(
    hass: HomeAssistant,
    config: dict[str, Any],
) -> TuyaCloudApi | TuyaLocalDevice:
    """Create the appropriate API client based on config."""
    if config.get("connection_type") == CONNECTION_TYPE_LOCAL:
        return TuyaLocalDevice(
            hass=hass,
            device_id=config["device_id"],
            local_key=config["local_key"],
            ip_address=config["ip_address"],
        )
    return TuyaCloudApi(
        hass=hass,
        access_key=config["access_key"],
        secret_key=config["secret_key"],
        device_id=config["device_id"],
        region=config["region"],
    )
