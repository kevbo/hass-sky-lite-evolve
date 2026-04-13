"""Tests for the Sky Lite Evolve number platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.sky_lite_evolve.const import (
    DPS_LASER_BRIGHTNESS,
    DPS_ROTATION,
    LASER_BRIGHTNESS_MAX,
    LASER_BRIGHTNESS_MIN,
    ROTATION_SPEED_MAX,
    ROTATION_SPEED_MIN,
)
from custom_components.sky_lite_evolve.number import (
    SkyLiteEvolveLaserBrightness,
    SkyLiteEvolveRotationSpeed,
)


def _make_coordinator(data=None):
    coord = MagicMock()
    coord.device_id = "test_device_id"
    coord.data = data
    coord.async_send_command = AsyncMock()
    coord.async_add_listener = MagicMock(return_value=MagicMock())
    return coord


def _make_entry():
    entry = MagicMock()
    entry.title = "Sky Lite Evolve"
    return entry


# ---------------------------------------------------------------------------
# Laser Brightness
# ---------------------------------------------------------------------------


class TestLaserBrightness:
    """Tests for SkyLiteEvolveLaserBrightness."""

    def _create(self, data=None):
        coord = _make_coordinator(data)
        entry = _make_entry()
        return SkyLiteEvolveLaserBrightness(coord, entry), coord

    def test_unique_id(self) -> None:
        num, _ = self._create()
        assert num.unique_id == "test_device_id_laser_brightness"

    def test_native_value_none_data(self) -> None:
        num, _ = self._create(data=None)
        assert num.native_value is None

    def test_native_value_no_key(self) -> None:
        num, _ = self._create(data={})
        assert num.native_value is None

    def test_native_value(self) -> None:
        num, _ = self._create(data={DPS_LASER_BRIGHTNESS: 500})
        assert num.native_value == 50

    def test_native_value_min(self) -> None:
        num, _ = self._create(data={DPS_LASER_BRIGHTNESS: 10})
        assert num.native_value == 1

    @pytest.mark.asyncio
    async def test_set_native_value(self) -> None:
        num, coord = self._create(data={DPS_LASER_BRIGHTNESS: 500})
        await num.async_set_native_value(50)
        coord.async_send_command.assert_called_once_with(DPS_LASER_BRIGHTNESS, 500)

    @pytest.mark.asyncio
    async def test_set_native_value_clamped_low(self) -> None:
        num, coord = self._create(data={})
        await num.async_set_native_value(0)
        coord.async_send_command.assert_called_once_with(
            DPS_LASER_BRIGHTNESS, LASER_BRIGHTNESS_MIN
        )

    @pytest.mark.asyncio
    async def test_set_native_value_clamped_high(self) -> None:
        num, coord = self._create(data={})
        await num.async_set_native_value(200)
        coord.async_send_command.assert_called_once_with(
            DPS_LASER_BRIGHTNESS, LASER_BRIGHTNESS_MAX
        )


# ---------------------------------------------------------------------------
# Rotation Speed
# ---------------------------------------------------------------------------


class TestRotationSpeed:
    """Tests for SkyLiteEvolveRotationSpeed."""

    def _create(self, data=None):
        coord = _make_coordinator(data)
        entry = _make_entry()
        return SkyLiteEvolveRotationSpeed(coord, entry), coord

    def test_unique_id(self) -> None:
        num, _ = self._create()
        assert num.unique_id == "test_device_id_rotation_speed"

    def test_native_value_none_data(self) -> None:
        num, _ = self._create(data=None)
        assert num.native_value is None

    def test_native_value_no_key(self) -> None:
        num, _ = self._create(data={})
        assert num.native_value is None

    def test_native_value(self) -> None:
        num, _ = self._create(data={DPS_ROTATION: 50})
        assert num.native_value == 50

    @pytest.mark.asyncio
    async def test_set_native_value(self) -> None:
        num, coord = self._create(data={DPS_ROTATION: 50})
        await num.async_set_native_value(75)
        coord.async_send_command.assert_called_once_with(DPS_ROTATION, 75)

    @pytest.mark.asyncio
    async def test_set_native_value_clamped_low(self) -> None:
        num, coord = self._create(data={})
        await num.async_set_native_value(0)
        coord.async_send_command.assert_called_once_with(
            DPS_ROTATION, ROTATION_SPEED_MIN
        )

    @pytest.mark.asyncio
    async def test_set_native_value_clamped_high(self) -> None:
        num, coord = self._create(data={})
        await num.async_set_native_value(200)
        coord.async_send_command.assert_called_once_with(
            DPS_ROTATION, ROTATION_SPEED_MAX
        )
