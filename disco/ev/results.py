from __future__ import annotations
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd



class EVHostingCapacityResults:
    def __init__(self, v_df, th_df, plot_df, output_dir, feeder_name):
        self._v_df = v_df
        self._th_df = th_df
        self._plot_df = plot_df
        self._output_dir = Path(output_dir)
        self._feeder_name = feeder_name

    # def hosting_capacity(self) -> pd.DataFrame:
    #     v_max = self._v_df.set_index("Bus")["Maximum_kW"]
    #     th_max = self._th_df.set_index("Bus")["Maximum_kW"]

    #     buses = self._th_df["Bus"].values
    #     v_max_vals = v_max.reindex(buses).values
    #     th_max_vals = th_max.reindex(buses).values
    #     initial_kw = self._th_df["Initial_kW"].values

    #     combined_max = np.minimum(v_max_vals, th_max_vals)
    #     hc_kw = np.maximum(combined_max - initial_kw, 0.0)
    #     binding = np.where(v_max_vals <= th_max_vals, "voltage", "thermal")

    #     return pd.DataFrame({
    #         #"Load": loads,
    #         "Bus": buses,
    #         "Initial_kW": initial_kw,
    #         "Hosting_capacity_kW": hc_kw,
    #         "Binding_constraint": binding,
    #     })

    def summary(self) -> str:
        hc = self.hosting_capacity()
        n_total = len(hc)
        n_voltage = int((hc["Binding_constraint"] == "voltage").sum())
        n_thermal = int((hc["Binding_constraint"] == "thermal").sum())
        hc_kw = hc["Hosting_capacity_kW"]
        meta = self.simulation_metadata()
        duration = meta.get("runtime_seconds")
        duration_str = f"{float(duration):.2f} seconds" if duration is not None else "unknown"

        title = f"EV Hosting Capacity Summary — {self._feeder_name} Feeder"
        lines = [
            title,
            "=" * len(title),
            f"Runtime:             {duration_str}",
            f"Nodes analyzed:      {n_total}",
            f"Voltage-limited:     {n_voltage} nodes",
            f"Thermal-limited:     {n_thermal} nodes",
            f"Median capacity:     {hc_kw.median():.0f} kW",
            f"Mean capacity:       {hc_kw.mean():.0f} kW",
            f"Min capacity:        {hc_kw.min():.0f} kW",
            f"Max capacity:        {hc_kw.max():.0f} kW",
        ]
        return "\n".join(lines)
 

    def __repr__(self) -> str:
        return self.summary()
    
       
    @property
    def db_path(self) -> Path:
        return self._output_dir / "disco_ev_hc.db"
    
    def _read_table(self, table: str) -> pd.DataFrame:
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql(f"SELECT * FROM {table}", conn)
    def hosting_capacity(self) -> pd.DataFrame:
        return self._read_table("hosting_capacity")




    def voltage_screen(self) -> pd.DataFrame:
        return self._read_table("voltage_screen")
    
    def thermal_screen(self) -> pd.DataFrame:
        return self._read_table("thermal_screen")


    def chargers(self) -> pd.DataFrame:
        return self._read_table("chargers")

    def bus_distances(self) -> pd.DataFrame:
        return self._read_table("bus_distances")

    def simulation_metadata(self) -> dict[str, str]:
        df = self._read_table("simulation_metadata")
        return dict(zip(df["key"], df["value"]))
    
    def bus_coordinates(self) -> pd.DataFrame:
        return self._read_table("bus_coordinates")
    def line_segments(self) -> pd.DataFrame:
        return self._read_table("line_segments")
    @property
    def plots(self) -> "EVHostingCapacityPlots":
        from .plots import EVHostingCapacityPlots
        return EVHostingCapacityPlots(self)
    




    @classmethod
    def from_db(cls, output_dir) -> "EVHostingCapacityResults":
        """Load a past run's results from disco_ev_hc.db without re-simulating.

        Reads voltage_screen, thermal_screen, and simulation_metadata into
        a fresh EVHostingCapacityResults instance — bypassing __init__ since
        we don't have the in-memory DataFrames the constructor expects.
        """
        output_dir = Path(output_dir)
        inst = cls.__new__(cls)              # bypass __init__
        inst._output_dir = output_dir
        inst._plot_df = None                 # not stored in DB
        inst._feeder_name = inst.simulation_metadata().get("feeder_name", "unknown")
        inst._v_df = None #inst.voltage_screen()
        inst._th_df = None #inst.thermal_screen()
        return inst

