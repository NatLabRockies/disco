from __future__ import annotations
from pathlib import Path

from .config import Feeder
from .results import EVHostingCapacityResults



class EVHostingCapacity:
    def __init__(self, feeder: Feeder, num_cpus: int = None):
        self.feeder = feeder
        self.num_cpus = num_cpus

    def run(self, output_dir: str = "results/ev_hc") -> EVHostingCapacityResults:
        from disco.ev.feeder_EV_HC import run as _legacy_run

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        self.feeder.validate()

        v_df, th_df, plot_df = _legacy_run(
            master_file=self.feeder.master_file,
            feeder_name = self.feeder.name,
            lower_voltage_limit=0.95,
            upper_voltage_limit=1.05,
            kw_step_voltage_violation=10.0,
            voltage_tolerance=10.0,
            kw_step_thermal_violation=10.0,
            thermal_tolerance=10.0,
            extra_percentage_for_existing_overloads=2.0,
            thermal_loading_limit=100.0,
            export_circuit_elements=False,
            output_dir=output_dir,
            num_cpus=self.num_cpus,
        )

        return EVHostingCapacityResults(
            v_df=v_df,
            th_df=th_df,
            plot_df=plot_df,
            output_dir=output_dir,
            feeder_name=self.feeder.name,
        )

    def __repr__(self) -> str:
        return f"EVHostingCapacity(feeder={self.feeder.name!r}, num_cpus={self.num_cpus!r})"
