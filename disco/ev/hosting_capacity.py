from __future__ import annotations
from pathlib import Path

from .config import Feeder, EVHostingCapacityConfig
from .results import EVHostingCapacityResults



class EVHostingCapacity:
    def __init__(self, feeder: Feeder, num_cpus: int = None):
        self.feeder = feeder
        self.num_cpus = num_cpus

    def run(
            self, 
            output_dir: str = "results/ev_hc",
            config: EVHostingCapacityConfig | None = None,
            ) -> EVHostingCapacityResults:
        
        

        from disco.ev.feeder_EV_HC import run as _legacy_run
        
        config = config or EVHostingCapacityConfig()
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        self.feeder.validate()

        v_df, th_df, plot_df = _legacy_run(
            master_file=self.feeder.master_file,
            feeder_name=self.feeder.name,
            lower_voltage_limit=config.voltage_lower_limit_pu,
            upper_voltage_limit=config.voltage_upper_limit_pu,
            kw_step_voltage_violation=config.voltage_step_kw,
            voltage_tolerance=config.voltage_search_tolerance_kw,
            kw_step_thermal_violation=config.thermal_step_kw,
            thermal_tolerance=config.thermal_search_tolerance_kw,
            extra_percentage_for_existing_overloads=config.existing_overload_headroom_percent,
            thermal_loading_limit=config.thermal_loading_limit_percent,
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
