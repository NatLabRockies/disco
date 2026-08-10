from __future__ import annotations
from pathlib import Path
from datetime import datetime

from .config import Feeder, EVHostingCapacityConfig
from .hosting_capacity import EVHostingCapacity
from .dynamic_hc_model import build_dynamic_hc_models, datetime_to_dss_time
from .dynamic_results import merge_timestamp_hosting_capacity, DynamicEVHostingCapacityResults


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
        
        if not self.timestamps:
            raise ValueError("Dynamic EV HC requires at least one timestamp.")

        labels = []
        for ts in self.timestamps:
            if not isinstance(ts, datetime):
                raise TypeError(
                    f"timestamps must contain datetime objects, got {type(ts).__name__}: {ts!r}"
                )
            labels.append(ts.strftime("%Y%m%d_%H%M"))

        duplicate_labels = {label for label in labels if labels.count(label) > 1}
        if duplicate_labels:
            raise ValueError(
                f"Duplicate timestamp labels are not allowed: {sorted(duplicate_labels)}"
            )

        # Phase 1: freeze all timestamps with one compile (loadshapes parsed once)
        specs = [
            (datetime_to_dss_time(ts.year, ts.month, ts.day, ts.hour, ts.minute), label)
            for ts, label in zip(self.timestamps, labels)
        ]
        masters = build_dynamic_hc_models(self.feeder.master_file, specs, output_dir)

        # Phase 2: screen each frozen model
        dfs, per_ts = {}, {}
        for label in labels:
            ts_dir = output_dir / label
            res = EVHostingCapacity(
                Feeder(masters[label], name=f"{self.feeder.name}_{label}"),
                num_cpus=self.num_cpus, config=self.config,
            ).run(ts_dir)

            per_ts[label] = res
            dfs[label] = res.hosting_capacity()     # Bus, Initial_kW, Hosting_capacity_kW, Binding_constraint
            print(f"[{label}] done")


        merged = merge_timestamp_hosting_capacity(dfs, key_cols=["Bus"])
        merged.to_csv(output_dir / "dynamic_ev_hc.csv", index=False)
        return DynamicEVHostingCapacityResults(merged, per_ts, output_dir)

    def __repr__(self) -> str:
        return (f"DynamicEVHostingCapacity(feeder={self.feeder.name!r}, "
                f"timestamps={len(self.timestamps)})")
