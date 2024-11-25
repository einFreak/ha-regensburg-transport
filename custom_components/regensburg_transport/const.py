"""Constants for the Regensburg Transport integration."""

from datetime import timedelta

DOMAIN = "regensburg_transport"
SCAN_INTERVAL = timedelta(seconds=60 * 2)
API_ENDPOINT = "https://efa.rvv.de/efa"
API_MAX_RESULTS = 5

DEFAULT_ICON = "mdi:clock"
BUS_ICON = "mdi:bus"

CONF_DEPARTURES = "departures"
CONF_DEPARTURES_NAME = "name"
CONF_DEPARTURES_SHORT_NAME = "shortName"
CONF_DEPARTURES_STOP_ID = "stop_id"
