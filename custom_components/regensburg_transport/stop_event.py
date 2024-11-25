"""Module for handling stop events in Regensburg transport."""

# pylint: disable=duplicate-code
from dataclasses import dataclass
from datetime import datetime, timedelta

from .const import DEFAULT_ICON


@dataclass
class StopEvent:
    """Represents a stop event with details about departure, transportation, and timings."""

    departure_point: str
    transportation_nr: int
    transportation_direction: str
    planned: datetime
    estimated: datetime
    gap: int

    icon: str = DEFAULT_ICON

    def __rvv_to_datetime(self):
        timestamp = datetime.fromisoformat(self)
        return timestamp + timedelta(hours=2)

    @classmethod
    def from_dict(cls, source):
        """Create a StopEvent instance from a dictionary."""
        dep_name = source.get("location").get("name")
        dep_nr = source.get("transportation").get("number")
        dep_dir = source.get("transportation").get("destination").get("name")

        dep_planned = cls.__rvv_to_datetime(source.get("departureTimePlanned"))
        dep_estimated = dep_planned
        if source.get("departureTimeEstimated"):
            dep_estimated = cls.__rvv_to_datetime(source.get("departureTimeEstimated"))

        dep_gap = round((dep_estimated - dep_planned).total_seconds() / 60)

        return cls(
            departure_point=dep_name,
            transportation_nr=dep_nr,
            transportation_direction=dep_dir,
            planned=dep_planned,
            estimated=dep_estimated,
            gap=dep_gap,
            icon=DEFAULT_ICON,
        )

    def to_dict(self):
        """Convert the StopEvent instance to a dictionary."""
        return {
            "departurePoint": self.departure_point,
            "transportationNr": self.transportation_nr,
            "transportationDirection": self.transportation_direction,
            "planned": self.planned,
            "estimated": self.estimated,
            "gap": self.gap,
        }

    def to_string(self):
        """Convert the StopEvent instance to a dictionary."""
        est_time = self.estimated.strftime("%H:%M")
        str_stop = (
            self.transportation_nr
            + " "
            + self.transportation_direction
            + ": "
            + est_time
            + " ("
            + str(self.gap)
            + "min delay)"
        )
        return {
            str_stop,
        }
