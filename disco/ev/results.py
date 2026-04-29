from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd


class EVHostingCapacityResults:
    def __init__(self, v_df, th_df, plot_df, output_dir, feeder_name):
        self._v_df = v_df
        self._th_df = th_df
        self._plot_df = plot_df
        self._output_dir = Path(output_dir)
        self._feeder_name = feeder_name

    def hosting_capacity(self) -> pd.DataFrame:
        v_max = self._v_df.set_index("Load")["Maximum_kW"]
        th_max = self._th_df.set_index("Load")["Maximum_kW"]

        loads = self._th_df["Load"].values
        v_max_vals = v_max.reindex(loads).values
        th_max_vals = th_max.reindex(loads).values
        initial_kw = self._th_df["Initial_kW"].values

        combined_max = np.minimum(v_max_vals, th_max_vals)
        hc_kw = np.maximum(combined_max - initial_kw, 0.0)
        binding = np.where(v_max_vals <= th_max_vals, "voltage", "thermal")

        return pd.DataFrame({
            "Load": loads,
            "Bus": self._th_df["Bus"].values,
            "Initial_kW": initial_kw,
            "Hosting_capacity_kW": hc_kw,
            "Binding_constraint": binding,
        })

    def summary(self) -> str:
        hc = self.hosting_capacity()
        n_total = len(hc)
        n_voltage = int((hc["Binding_constraint"] == "voltage").sum())
        n_thermal = int((hc["Binding_constraint"] == "thermal").sum())
        hc_kw = hc["Hosting_capacity_kW"]

        title = f"EV Hosting Capacity Summary — {self._feeder_name} Feeder"
        lines = [
            title,
            "=" * len(title),
            f"Nodes analyzed:      {n_total}",
            f"Voltage-limited:     {n_voltage} nodes",
            f"Thermal-limited:     {n_thermal} nodes",
            f"Median capacity:     {hc_kw.median():.0f} kW",
            f"Mean capacity:       {hc_kw.mean():.0f} kW",
            f"Min capacity:        {hc_kw.min():.0f} kW",
            f"Max capacity:        {hc_kw.max():.0f} kW",
        ]
        return "\n".join(lines)

    # def __repr__(self) -> str:
    #     return (
    #         f"EVHostingCapacityResults("
    #         f"feeder={self._feeder_name!r}, "
    #         f"nodes={len(self._th_df)}, "
    #         f"output_dir={str(self._output_dir)!r})"
    #     )
    def __repr__(self) -> str:
        return self.summary()