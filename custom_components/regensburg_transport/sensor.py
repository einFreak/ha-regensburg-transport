# pylint: disable=duplicate-code
"""Regensburg (RVV) transport integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (  # pylint: disable=unused-import
    API_ENDPOINT,
    API_MAX_RESULTS,
    BUS_ICON,
    CONF_DEPARTURES,
    CONF_DEPARTURES_NAME,
    CONF_DEPARTURES_SHORT_NAME,
    CONF_DEPARTURES_STOP_ID,
    DEFAULT_ICON,
    DOMAIN,  # noqa: F401
    SCAN_INTERVAL,  # noqa: F401
)
from .stop_event import StopEvent

_LOGGER = logging.getLogger(__name__)

SENSOR_PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_DEPARTURES): [
            {
                vol.Required(CONF_DEPARTURES_NAME): cv.string,
                vol.Required(CONF_DEPARTURES_STOP_ID): cv.string,
            }
        ]
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    _: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform from a YAML configuration file ."""
    if CONF_DEPARTURES in config:
        for departure in config[CONF_DEPARTURES]:
            add_entities(
                [
                    NextDepartureSensor(hass, departure),
                    DelaySensor(hass, departure),
                ],
                True,
            )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform through the Home Assistant UI (Config Flow)."""
    _LOGGER.debug("async_setup_entry: %s", config_entry.options)
    config_data = dict(config_entry.data)
    async_add_entities(
        [
            NextDepartureSensor(hass, config_data),
            DelaySensor(hass, config_data),
        ]
    )


class RegensburgTransportSensor(SensorEntity):
    """Storing and updating RVV data to be used in sensor entities."""

    stop_events: list[StopEvent] = []

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.stop_id)},
            name=self.sensor_name,
            manufacturer="RVV",
            model="Station Sensor",
            model_id=self.stop_id,
        )

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the TransportSensor.

        Args:
            hass (HomeAssistant): The Home Assistant instance.
            config (dict): The configuration dictionary.

        """
        self.hass: HomeAssistant = hass
        self.config: dict = config
        self.stop_id: str = config[CONF_DEPARTURES_STOP_ID]
        self.sensor_name: str | None = config.get(CONF_DEPARTURES_NAME)
        self.sensor_shortname: str | None = config.get(CONF_DEPARTURES_SHORT_NAME)
        self._state: str | None = None

    async def async_update(self) -> None:
        """Update the sensor state."""
        RegensburgTransportSensor.stop_events = await self.parse_departures()

    async def fetch_departures(self):
        """Fetch the departures from the API and return the JSON response."""
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                url=f"{API_ENDPOINT}/XML_DM_REQUEST",
                params={
                    "mode": "direct",
                    "outputFormat": "rapidJSON",
                    "type_dm": "any",
                    "useRealtime": "1",
                    "name_dm": "de:09362:12009",
                    "limit": API_MAX_RESULTS,
                },
                timeout=30,
            ) as response,
        ):
            response.raise_for_status()
            return await response.json()

    async def parse_departures(self) -> list[StopEvent]:
        """Parse the departures from the API response and return a list of StopEvent objects."""
        try:
            response = await self.fetch_departures()
        except aiohttp.ClientError as ex:
            _LOGGER.warning("API error: %s", ex)
            return []

        _LOGGER.debug("OK: departures for %s: %s", self.stop_id, response)

        # parse JSON response
        try:
            departures = response.get("stopEvents")
        except aiohttp.ClientResponseError as ex:
            _LOGGER.error("API invalid JSON: %s", ex)
            return []

        # convert api data into objects
        unsorted = [StopEvent.from_dict(departure) for departure in departures]
        return sorted(unsorted, key=lambda d: d.planned)


class NextDepartureSensor(RegensburgTransportSensor):
    """Representation of a transport sensor."""

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            await super().async_update()
            next_departure = self.next_departure()
        except aiohttp.ClientError as ex:
            _LOGGER.warning("API error: %s", ex)
            self._attr_available = False
            return

        if next_departure:
            self._attr_available = True
            hour_str = f"{next_departure.estimated.hour:d}:{next_departure.estimated.minute:02d}"
            self._attr_native_value = f"{next_departure.transportation_nr} {next_departure.transportation_direction} at {hour_str}"
        self._attr_native_value = "N/A"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"Next Departure {self.sensor_shortname}"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        # next_departure = self.next_departure()
        # return next_departure.icon if next_departure else BUS_ICON
        return BUS_ICON

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the sensor."""
        return f"stop_{self.stop_id}_departures"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        next_departure = self.next_departure()
        if next_departure:
            hour_str = f"{next_departure.estimated.hour:d}:{next_departure.estimated.minute:02d}"
            return f"{next_departure.transportation_nr} {next_departure.transportation_direction} at {hour_str}"
        return "N/A"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes of the sensor."""
        return {
            "departures": [
                event.to_string()
                for event in RegensburgTransportSensor.stop_events or []
            ]
        }

    def next_departure(self) -> StopEvent | None:
        """Return the next departure event."""
        if RegensburgTransportSensor.stop_events and isinstance(
            RegensburgTransportSensor.stop_events, list
        ):
            return RegensburgTransportSensor.stop_events[0]
        return None


class DelaySensor(RegensburgTransportSensor):
    """Representation of a transport sensor."""

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            await super().async_update()
            next_departure = self.next_departure()
        except aiohttp.ClientError as ex:
            _LOGGER.warning("API error: %s", ex)
            self._attr_available = False
            return

        if next_departure:
            self._attr_available = True
            dif = next_departure.estimated - next_departure.planned
            minute_diff = dif.total_seconds() / 60
            self._attr_native_value = int(minute_diff)
        self._attr_native_value = 0

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        # return self.sensor_name or f"Stop ID: {self.stop_id}"
        return f"Delay {self.sensor_shortname}"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        next_departure = self.next_departure()
        return next_departure.icon if next_departure else DEFAULT_ICON

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the sensor."""
        return f"stop_{self.stop_id}_delay"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        next_departure = self.next_departure()
        if next_departure:
            dif = next_departure.estimated - next_departure.planned
            minute_diff = dif.total_seconds() / 60
            return int(minute_diff)
        return 0

    def next_departure(self) -> StopEvent | None:
        """Return the next departure event."""
        if RegensburgTransportSensor.stop_events and isinstance(
            RegensburgTransportSensor.stop_events, list
        ):
            return RegensburgTransportSensor.stop_events[0]
        return None
