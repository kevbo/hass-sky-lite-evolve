"""Tests for the Sky Lite Evolve switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.sky_lite_evolve.const import (
    DPS_LASER_STATE,
    DPS_MOTOR_STATE,
    DPS_POWER,
)
from custom_components.sky_lite_evolve.switch import (
    SkyLiteEvolveLaserSwitch,
    SkyLiteEvolveMotorSwitch,
)


def _make_coordinator(data=None):
    coord = MagicMock()
    coord.device_id = "test_device_id"
    coord.data = data
    coord.async_send_command = AsyncMock()
    coord.async_send_commands = AsyncMock()
    coord.async_add_listener = MagicMock(return_value=MagicMock())
    return coord


def _make_entry():
    entry = MagicMock()
    entry.title = "Sky Lite Evolve"
    return entry


# ---------------------------------------------------------------------------
# Laser Switch
# ---------------------------------------------------------------------------


class TestLaserSwitch:
    """Tests for SkyLiteEvolveLaserSwitch."""

    def _create(self, data=None):
        coord = _make_coordinator(data)
        entry = _make_entry()
        return SkyLiteEvolveLaserSwitch(coord, entry), coord

    def test_unique_id(self) -> None:
        sw, _ = self._create()
        assert sw.unique_id == "test_device_id_laser_switch"

    def test_is_on_none_data(self) -> None:
        sw, _ = self._create(data=None)
        assert sw.is_on is None

    def test_is_on_no_power(self) -> None:
        sw, _ = self._create(data={})
        assert sw.is_on is None

    def test_is_on_no_laser(self) -> None:
        sw, _ = self._create(data={DPS_POWER: True})
        assert sw.is_on is None

    def test_is_on_true(self) -> None:
        sw, _ = self._create(data={DPS_POWER: True, DPS_LASER_STATE: True})
        assert sw.is_on is True

    def test_is_on_false_power_off(self) -> None:
        sw, _ = self._create(data={DPS_POWER: False, DPS_LASER_STATE: True})
        assert sw.is_on is False

    def test_is_on_false_laser_off(self) -> None:
        sw, _ = self._create(data={DPS_POWER: True, DPS_LASER_STATE: False})
        assert sw.is_on is False

    @pytest.mark.asyncio
    async def test_turn_on_powers_up(self) -> None:
        sw, coord = self._create(data={DPS_POWER: False, DPS_LASER_STATE: False})
        await sw.async_turn_on()
        args = coord.async_send_commands.call_args[0][0]
        assert args[DPS_POWER] is True
        assert args[DPS_LASER_STATE] is True

    @pytest.mark.asyncio
    async def test_turn_on_already_powered(self) -> None:
        sw, coord = self._create(data={DPS_POWER: True, DPS_LASER_STATE: False})
        await sw.async_turn_on()
        args = coord.async_send_commands.call_args[0][0]
        assert DPS_POWER not in args
        assert args[DPS_LASER_STATE] is True

    @pytest.mark.asyncio
    async def test_turn_off(self) -> None:
        sw, coord = self._create(data={DPS_POWER: True, DPS_LASER_STATE: True})
        await sw.async_turn_off()
        coord.async_send_command.assert_called_once_with(DPS_LASER_STATE, False)


# ---------------------------------------------------------------------------
# Motor Switch
# ---------------------------------------------------------------------------


class TestMotorSwitch:
    """Tests for SkyLiteEvolveMotorSwitch."""

    def _create(self, data=None):
        coord = _make_coordinator(data)
        entry = _make_entry()
        return SkyLiteEvolveMotorSwitch(coord, entry), coord

    def test_unique_id(self) -> None:
        sw, _ = self._create()
        assert sw.unique_id == "test_device_id_motor_switch"

    def test_is_on_none_data(self) -> None:
        sw, _ = self._create(data=None)
        assert sw.is_on is None

    def test_is_on_no_power(self) -> None:
        sw, _ = self._create(data={})
        assert sw.is_on is None

    def test_is_on_no_motor(self) -> None:
        sw, _ = self._create(data={DPS_POWER: True})
        assert sw.is_on is None

    def test_is_on_true(self) -> None:
        sw, _ = self._create(data={DPS_POWER: True, DPS_MOTOR_STATE: True})
        assert sw.is_on is True

    def test_is_on_false_power_off(self) -> None:
        sw, _ = self._create(data={DPS_POWER: False, DPS_MOTOR_STATE: True})
        assert sw.is_on is False

    @pytest.mark.asyncio
    async def test_turn_on_powers_up(self) -> None:
        sw, coord = self._create(data={DPS_POWER: False, DPS_MOTOR_STATE: False})
        await sw.async_turn_on()
        args = coord.async_send_commands.call_args[0][0]
        assert args[DPS_POWER] is True
        assert args[DPS_MOTOR_STATE] is True

    @pytest.mark.asyncio
    async def test_turn_on_already_powered(self) -> None:
        sw, coord = self._create(data={DPS_POWER: True, DPS_MOTOR_STATE: False})
        await sw.async_turn_on()
        args = coord.async_send_commands.call_args[0][0]
        assert DPS_POWER not in args
        assert args[DPS_MOTOR_STATE] is True

    @pytest.mark.asyncio
    async def test_turn_off(self) -> None:
        sw, coord = self._create(data={DPS_POWER: True, DPS_MOTOR_STATE: True})
        await sw.async_turn_off()
        coord.async_send_command.assert_called_once_with(DPS_MOTOR_STATE, False)
