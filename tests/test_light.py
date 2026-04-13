"""Tests for the Sky Lite Evolve light platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_HS_COLOR, ColorMode

from custom_components.sky_lite_evolve.const import (
    DPS_COLOR,
    DPS_COLOR_STATE,
    DPS_POWER,
)
from custom_components.sky_lite_evolve.light import (
    SkyLiteEvolveLight,
    _make_colour_data,
    _parse_colour_data,
)

# ---------------------------------------------------------------------------
# _parse_colour_data
# ---------------------------------------------------------------------------


class TestParseColourData:
    """Tests for _parse_colour_data."""

    def test_hex_string(self) -> None:
        assert _parse_colour_data("000003e803e8") == (0, 1000, 1000)

    def test_hex_string_nonzero(self) -> None:
        assert _parse_colour_data("00b401f400c8") == (180, 500, 200)

    def test_hex_invalid_chars(self) -> None:
        assert _parse_colour_data("xxxxxxxxxxxx") == (0, 1000, 1000)

    def test_json_string(self) -> None:
        assert _parse_colour_data('{"h": 120, "s": 500, "v": 800}') == (120, 500, 800)

    def test_dict(self) -> None:
        assert _parse_colour_data({"h": 240, "s": 900, "v": 100}) == (240, 900, 100)

    def test_dict_defaults(self) -> None:
        assert _parse_colour_data({}) == (0, 1000, 1000)

    def test_non_string_non_dict(self) -> None:
        assert _parse_colour_data(12345) == (0, 1000, 1000)

    def test_none(self) -> None:
        assert _parse_colour_data(None) == (0, 1000, 1000)

    def test_short_string_not_json(self) -> None:
        assert _parse_colour_data("abc") == (0, 1000, 1000)

    def test_json_non_dict(self) -> None:
        assert _parse_colour_data("[1, 2, 3]") == (0, 1000, 1000)


# ---------------------------------------------------------------------------
# _make_colour_data
# ---------------------------------------------------------------------------


class TestMakeColourData:
    """Tests for _make_colour_data."""

    def test_basic(self) -> None:
        assert _make_colour_data(180, 500, 200) == {"h": 180, "s": 500, "v": 200}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _create_light(data=None):
    coord = _make_coordinator(data)
    entry = _make_entry()
    light = SkyLiteEvolveLight(coord, entry)
    return light, coord


# ---------------------------------------------------------------------------
# SkyLiteEvolveLight
# ---------------------------------------------------------------------------


class TestSkyLiteEvolveLight:
    """Tests for SkyLiteEvolveLight entity."""

    def test_unique_id(self) -> None:
        light, _ = _create_light()
        assert light.unique_id == "test_device_id_nebula_light"

    def test_color_mode(self) -> None:
        light, _ = _create_light()
        assert light._attr_color_mode == ColorMode.HS

    def test_is_on_none_data(self) -> None:
        light, _ = _create_light(data=None)
        assert light.is_on is None

    def test_is_on_no_power(self) -> None:
        light, _ = _create_light(data={})
        assert light.is_on is None

    def test_is_on_power_true_no_color_state(self) -> None:
        light, _ = _create_light(data={DPS_POWER: True})
        assert light.is_on is True

    def test_is_on_power_false(self) -> None:
        light, _ = _create_light(data={DPS_POWER: False})
        assert light.is_on is False

    def test_is_on_power_true_color_state_true(self) -> None:
        light, _ = _create_light(data={DPS_POWER: True, DPS_COLOR_STATE: True})
        assert light.is_on is True

    def test_is_on_power_true_color_state_false(self) -> None:
        light, _ = _create_light(data={DPS_POWER: True, DPS_COLOR_STATE: False})
        assert light.is_on is False

    def test_brightness_from_hex(self) -> None:
        light, _ = _create_light(data={DPS_COLOR: "000003e803e8"})
        assert light.brightness == 255

    def test_brightness_from_hex_low(self) -> None:
        light, _ = _create_light(data={DPS_COLOR: "000003e80064"})
        assert light.brightness == max(1, round(100 / 1000 * 255))

    def test_brightness_none_no_data(self) -> None:
        light, _ = _create_light(data=None)
        assert light.brightness is None

    def test_brightness_none_no_color(self) -> None:
        light, _ = _create_light(data={DPS_POWER: True})
        assert light.brightness is None

    def test_hs_color_from_hex(self) -> None:
        light, _ = _create_light(data={DPS_COLOR: "00b401f400c8"})
        assert light.hs_color == (180.0, 50.0)

    def test_hs_color_none_no_data(self) -> None:
        light, _ = _create_light(data=None)
        assert light.hs_color is None

    def test_hs_color_none_no_color(self) -> None:
        light, _ = _create_light(data={DPS_POWER: True})
        assert light.hs_color is None

    @pytest.mark.asyncio
    async def test_turn_on_basic(self) -> None:
        light, coord = _create_light(data={DPS_POWER: False, DPS_COLOR: "000003e803e8"})
        await light.async_turn_on()
        coord.async_send_commands.assert_called_once()
        args = coord.async_send_commands.call_args[0][0]
        assert args[DPS_POWER] is True
        assert args[DPS_COLOR_STATE] is True

    @pytest.mark.asyncio
    async def test_turn_on_already_on(self) -> None:
        light, coord = _create_light(data={DPS_POWER: True, DPS_COLOR: "000003e803e8"})
        await light.async_turn_on()
        args = coord.async_send_commands.call_args[0][0]
        assert DPS_POWER not in args

    @pytest.mark.asyncio
    async def test_turn_on_with_hs_color(self) -> None:
        light, coord = _create_light(data={DPS_POWER: True, DPS_COLOR: "000003e803e8"})
        await light.async_turn_on(**{ATTR_HS_COLOR: (120.0, 50.0)})
        args = coord.async_send_commands.call_args[0][0]
        assert args[DPS_COLOR] == {"h": 120, "s": 500, "v": 1000}

    @pytest.mark.asyncio
    async def test_turn_on_with_brightness(self) -> None:
        light, coord = _create_light(data={DPS_POWER: True, DPS_COLOR: "000003e803e8"})
        await light.async_turn_on(**{ATTR_BRIGHTNESS: 128})
        args = coord.async_send_commands.call_args[0][0]
        color = args[DPS_COLOR]
        assert color["v"] == max(10, int(128 / 255 * 1000))

    @pytest.mark.asyncio
    async def test_turn_on_no_current_color(self) -> None:
        light, coord = _create_light(data={DPS_POWER: False})
        await light.async_turn_on()
        args = coord.async_send_commands.call_args[0][0]
        assert args[DPS_POWER] is True
        assert args[DPS_COLOR_STATE] is True

    @pytest.mark.asyncio
    async def test_turn_off(self) -> None:
        light, coord = _create_light(data={DPS_POWER: True})
        await light.async_turn_off()
        coord.async_send_command.assert_called_once_with(DPS_COLOR_STATE, False)
