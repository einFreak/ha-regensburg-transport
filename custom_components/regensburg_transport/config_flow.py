"""Config flow for Regensburg Transport integration."""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    API_ENDPOINT,
    CONF_DEPARTURES_NAME,
    CONF_DEPARTURES_SHORT_NAME,
    CONF_DEPARTURES_STOP_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

CONF_SEARCH = "search"
CONF_FOUND_STOPS = "found_stops"
CONF_SELECTED_STOP = "selected_stop"

NAME_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SEARCH): cv.string,
    }
)


def get_stop_id(name) -> list[dict[str, Any]] | None:
    """Fetch stop IDs based on the provided name."""
    try:
        response = requests.get(
            url=f"{API_ENDPOINT}/XML_STOPFINDER_REQUEST",
            params={
                "commonMacro": "stopfinder",
                "outputFormat": "rapidJSON",
                "type_sf": "any",
                "name_sf": name,
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        _LOGGER.warning("API error: %s", ex)
        return []
    except requests.exceptions.Timeout as ex:
        _LOGGER.warning("API timeout: %s", ex)
        return []

    _LOGGER.debug("OK: stops for %s: %s", name, response.text)

    # parse JSON response
    try:
        stops = json.loads(response.text).get("locations")
    except json.JSONDecodeError as ex:
        _LOGGER.error("API invalid JSON: %s", ex)
        return []

    # convert api data into objects
    return [
        {
            CONF_DEPARTURES_NAME: stop.get("name"),
            CONF_DEPARTURES_STOP_ID: stop.get("id"),
            CONF_DEPARTURES_SHORT_NAME: stop.get("disassembledName"),
        }
        for stop in stops
        if stop.get("isGlobalId")
    ]


def list_stops(stops) -> vol.Schema | None:
    """Provide a drop down list of stops."""
    return vol.Schema(
        {
            vol.Required(CONF_SELECTED_STOP, default=False): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        f"{stop[CONF_DEPARTURES_NAME]} [{stop[CONF_DEPARTURES_STOP_ID]}]"
                        for stop in stops
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )

class TransportConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN): # type: ignore[call-arg]
    """Handle the config flow for Regensburg Transport integration."""

    VERSION = 1
    MINOR_VERSION = 1

    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Init the ConfigFlow."""
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # if user_input is not None:
        #     try:
        #         info = await validate_input(self.hass, user_input)
        #     except CannotConnect:
        #         errors["base"] = "cannot_connect"
        #     except InvalidAuth:
        #         errors["base"] = "invalid_auth"
        #     except Exception:
        #         _LOGGER.exception("Unexpected exception")
        #         errors["base"] = "unknown"
        #     else:
        #         return self.async_create_entry(title=info["title"], data=user_input)

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=NAME_SCHEMA,
                errors={},
            )
        self.data[CONF_FOUND_STOPS] = await self.hass.async_add_executor_job(
            get_stop_id, user_input[CONF_SEARCH]
        )

        _LOGGER.debug(
            "OK: found stops for %s: %s",
            user_input[CONF_SEARCH],
            self.data[CONF_FOUND_STOPS],
        )

        return await self.async_step_stop()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the reconfiguration."""
        return await self.async_step_user(user_input)

    async def async_step_stop(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="stop",
                data_schema=list_stops(self.data[CONF_FOUND_STOPS]),
                errors={},
            )

        selected_stop = next(
            (
                stop[CONF_DEPARTURES_NAME],
                stop[CONF_DEPARTURES_STOP_ID],
                stop[CONF_DEPARTURES_SHORT_NAME],
            )
            for stop in self.data[CONF_FOUND_STOPS]
            if user_input[CONF_SELECTED_STOP]
            == f"{stop[CONF_DEPARTURES_NAME]} [{stop[CONF_DEPARTURES_STOP_ID]}]"
        )
        (
            self.data[CONF_DEPARTURES_NAME],
            self.data[CONF_DEPARTURES_STOP_ID],
            self.data[CONF_DEPARTURES_SHORT_NAME],
        ) = selected_stop
        _LOGGER.debug("OK: selected stop %s [%s]", selected_stop[0], selected_stop[1])

        data = user_input
        data[CONF_DEPARTURES_STOP_ID] = self.data[CONF_DEPARTURES_STOP_ID]
        data[CONF_DEPARTURES_NAME] = self.data[CONF_DEPARTURES_NAME]
        data[CONF_DEPARTURES_SHORT_NAME] = self.data[CONF_DEPARTURES_SHORT_NAME]
        return self.async_create_entry(
            title=f"{data[CONF_DEPARTURES_NAME]} [{data[CONF_DEPARTURES_STOP_ID]}]",
            data=data,
        )
