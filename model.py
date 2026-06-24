from enum import Enum
from typing import Optional

from error import print_error

try:
    from pydantic import BaseModel, Field, model_validator
except ModuleNotFoundError as err:
    print_error(f"{err}. Please install it using 'pip install pydantic'.")

WINDOW_SIZE: tuple[int, int] = (1200, 800)


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone(BaseModel):
    name: str = Field()
    coordinate_x: int = Field()
    coordinate_y: int = Field()
    zone_type: ZoneType = Field(default=ZoneType.NORMAL)
    color: Optional[str] = Field(default=None)
    max_drones: int = Field(ge=1, default=1)

    @model_validator(mode='after')
    def _validate(self) -> 'Zone':
        if '-' in self.name or ' ' in self.name:
            raise ValueError(
                f"The zone name '{self.name}' "
                "must not contain hyphens or spaces."
            )
        return self


class Connection(BaseModel):
    first_zone: str = Field()
    second_zone: str = Field()
    max_link_capacity: int = Field(ge=1, default=1)

    @model_validator(mode='after')
    def _validate(self) -> 'Connection':
        if self.first_zone == self.second_zone:
            raise ValueError(
                f"An area cannot be connected to itself ('{self.first_zone}')."
            )
        return self
