from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union



class Feeder:
    def __init__(self, master_file, name=None):
        self.master_file = Path(master_file)
        self.name = name or self.master_file.parent.name

    @classmethod
    def from_opendss(cls, master_file) -> Feeder:
        return cls(master_file)

    # @classmethod
    # def from_gdm(cls, master_file) -> Feeder:
    #     return cls(master_file)

    def validate(self) -> bool:
        if not self.master_file.exists():
            raise FileNotFoundError(f"Master file not found: {self.master_file}")
        return True

    def __repr__(self) -> str:
        return f"Feeder(name={self.name!r}, master_file={str(self.master_file)!r})"



@dataclass
class EVHostingCapacityConfig:
    """Tunable parameters for EV Hosting Capacity analysis."""
    voltage_lower_limit_pu: float = 0.95
    voltage_upper_limit_pu: float = 1.05
    voltage_step_kw: float = 10.0
    voltage_search_tolerance_kw: float = 10.0

    thermal_loading_limit_percent: float = 100.0
    thermal_step_kw: float = 10.0
    thermal_search_tolerance_kw: float = 10.0
    existing_overload_headroom_percent: float = 5.0

