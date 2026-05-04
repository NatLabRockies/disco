from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
#from typing import Optional, Union



class Feeder:
    def __init__(self, master_file, name=None):
        self.master_file = Path(master_file)
        self.name = name or self.master_file.parent.name

    @classmethod
    def from_opendss(cls, master_file) -> Feeder:
        return cls(master_file)

    @classmethod
    def from_gdm(cls, gdm_path) -> Feeder:
        import sys

        from loguru import logger as _lg
        from gdm.distribution import DistributionSystem
        from ditto.writers.opendss.write import Writer

        _lg.remove()
        _lg.add(sys.stderr, level="ERROR")

        gdm_path = Path(gdm_path)
        export_dir = gdm_path.parent / (gdm_path.stem + "_opendss_export")
        export_dir.mkdir(exist_ok=True)
        system = DistributionSystem.from_json(gdm_path)
        Writer(system).write(
            output_path=export_dir,
            separate_substations=False,
            separate_feeders=False,
        )
        master_file = export_dir / "Master.dss"
        if not master_file.exists():
            raise FileNotFoundError(
                f"ditto export did not produce expected master file: {master_file}"
            )
        #print(f"  → wrote {master_file}")

        return cls(master_file=master_file, name=gdm_path.stem)

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

    thermal_loading_limit_percent: float = 120.0
    thermal_step_kw: float = 10.0
    thermal_search_tolerance_kw: float = 10.0
    existing_overload_headroom_percent: float = 5.0

