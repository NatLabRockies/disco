from __future__ import annotations
from pathlib import Path
from datetime import datetime

from .config import Feeder, EVHostingCapacityConfig
from .hosting_capacity import EVHostingCapacity
from .dynamic_hc_model import build_dynamic_hc_model, datetime_to_dss_time
from .dynamic_results import merge_and_range, DynamicEVHostingCapacityResults


class DynamicEVHostingCapacity:
    def __init__(self, feeder: Feeder, timestamps: list[datetime],
                 num_cpus=None, config: EVHostingCapacityConfig | None = None):
        self.feeder = feeder
        self.timestamps = timestamps
        self.num_cpus = num_cpus
        self.config = config or EVHostingCapacityConfig()

    def run(self, output_dir="results/ev_dhc") -> DynamicEVHostingCapacityResults:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        self.feeder.validate()

        dfs, per_ts = {}, {}
        for ts in self.timestamps:
            label = ts.strftime("%Y%m%d_%H%M")
            ts_dir = output_dir / label
            elapsed = datetime_to_dss_time(ts.year, ts.month, ts.day, ts.hour, ts.minute)

            master_ts = build_dynamic_hc_model(self.feeder.master_file, elapsed, ts_dir, label)
            res = EVHostingCapacity(
                Feeder(master_ts, name=f"{self.feeder.name}_{label}"),
                num_cpus=self.num_cpus, config=self.config,
            ).run(ts_dir)

            per_ts[label] = res
            dfs[label] = res.hosting_capacity()     # Bus, Initial_kW, Hosting_capacity_kW, Binding_constraint
            print(f"[{label}] done")

        merged = merge_and_range(dfs, key_cols=["Bus"])
        merged.to_csv(output_dir / "dynamic_ev_hc.csv", index=False)
        return DynamicEVHostingCapacityResults(merged, per_ts, output_dir)

    def __repr__(self) -> str:
        return (f"DynamicEVHostingCapacity(feeder={self.feeder.name!r}, "
                f"timestamps={len(self.timestamps)})")
