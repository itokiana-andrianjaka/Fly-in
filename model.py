"""Data model for zones and connections in the simulation."""

from enum import Enum

from error import print_error

try:
    from pydantic import BaseModel, Field, model_validator
except ModuleNotFoundError as err:
    print_error(str(err))

WINDOW_SIZE: tuple[int, int] = (1200, 800)


class ZoneType(Enum):
    """Enumeration of possible zone types."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone(BaseModel):
    """Data model for a zone in the simulation."""

    name: str = Field()
    coordinate_x: int = Field()
    coordinate_y: int = Field()
    zone_type: ZoneType = Field(default=ZoneType.NORMAL)
    color: str | None = Field(default=None)
    max_drones: int = Field(ge=1, default=1)

    @model_validator(mode='after')
    def _validate(self) -> 'Zone':
        """Validate the zone data."""
        if '-' in self.name or ' ' in self.name:
            raise ValueError(
                f"The zone name '{self.name}' "
                "must not contain hyphens or spaces."
            )
        return self


class Connection(BaseModel):
    """Data model for a connection between two zones in the simulation."""

    first_zone: str = Field()
    second_zone: str = Field()
    max_link_capacity: int = Field(ge=1, default=1)

    @model_validator(mode='after')
    def _validate(self) -> 'Connection':
        """Validate the connection data."""
        if self.first_zone == self.second_zone:
            raise ValueError(
                f"An area cannot be connected to itself ('{self.first_zone}')."
            )
        return self
