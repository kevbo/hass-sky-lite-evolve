"""Config flow for Sky Lite Evolve integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
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
    TUYA_REGIONS,
)
from .tuya_api import CannotConnect, InvalidAuth, TuyaCloudApi, TuyaLocalDevice

_LOGGER = logging.getLogger(__name__)


class SkyLiteEvolveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sky Lite Evolve."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - choose connection type."""
        if user_input is not None:
            if user_input[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_CLOUD:
                return await self.async_step_cloud()
            return await self.async_step_local()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONNECTION_TYPE, default=CONNECTION_TYPE_CLOUD
                    ): vol.In(
                        {
                            CONNECTION_TYPE_CLOUD: "Tuya Cloud API",
                            CONNECTION_TYPE_LOCAL: "Local (tinytuya)",
                        }
                    ),
                }
            ),
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle cloud configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                api = TuyaCloudApi(
                    hass=self.hass,
                    access_key=user_input[CONF_ACCESS_KEY],
                    secret_key=user_input[CONF_SECRET_KEY],
                    device_id=user_input[CONF_DEVICE_ID],
                    region=user_input[CONF_REGION],
                )
                device_info = await api.get_device_info()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during cloud setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=device_info.get("name", "Sky Lite Evolve"),
                    data={
                        CONF_CONNECTION_TYPE: CONNECTION_TYPE_CLOUD,
                        CONF_ACCESS_KEY: user_input[CONF_ACCESS_KEY],
                        CONF_SECRET_KEY: user_input[CONF_SECRET_KEY],
                        CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                        CONF_REGION: user_input[CONF_REGION],
                    },
                )

        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_KEY): str,
                    vol.Required(CONF_SECRET_KEY): str,
                    vol.Required(CONF_DEVICE_ID): str,
                    vol.Required(CONF_REGION, default="us"): vol.In(TUYA_REGIONS),
                }
            ),
            errors=errors,
        )

    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handle local connection configuration.

        Takes cloud credentials + IP to auto-fetch the local key,
        then validates with a local connection before saving.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Step 1: Fetch local_key via cloud API
            local_key = None
            try:
                api = TuyaCloudApi(
                    hass=self.hass,
                    access_key=user_input[CONF_ACCESS_KEY],
                    secret_key=user_input[CONF_SECRET_KEY],
                    device_id=user_input[CONF_DEVICE_ID],
                    region=user_input[CONF_REGION],
                )
                device_info = await api.get_device_info()
                local_key = device_info.get("local_key")
                if not local_key:
                    errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error fetching local key")
                errors["base"] = "unknown"

            # Step 2: Validate local connection
            if local_key and not errors:
                try:
                    device = TuyaLocalDevice(
                        hass=self.hass,
                        device_id=user_input[CONF_DEVICE_ID],
                        local_key=local_key,
                        ip_address=user_input[CONF_IP_ADDRESS],
                    )
                    await device.get_device_status()
                    await device.close()
                except Exception:
                    _LOGGER.exception("Local connection failed")
                    errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=device_info.get("name", "Sky Lite Evolve"),
                    data={
                        CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL,
                        CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                        CONF_LOCAL_KEY: local_key,
                        CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                    },
                )

        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_KEY): str,
                    vol.Required(CONF_SECRET_KEY): str,
                    vol.Required(CONF_DEVICE_ID): str,
                    vol.Required(CONF_REGION, default="us"): vol.In(TUYA_REGIONS),
                    vol.Required(CONF_IP_ADDRESS): str,
                }
            ),
            errors=errors,
        )
