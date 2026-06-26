# -*- coding: utf-8 -*-
"""Merge per-timestamp EV hosting-capacity tables into a Dynamic HC range result.

`merge_and_range` is a port of the user's `get_final_hc_table`
(process_hc_result_dfs.py): it joins each timestamp's hosting_capacity() table on
the key column(s), suffixes the result columns with the timestamp label, and computes
per-node Min/Max columns (the dynamic hosting-capacity flexibility range).
"""

from pathlib import Path
from functools import reduce

import pandas as pd


def merge_and_range(dfs: dict, key_cols) -> pd.DataFrame:
    key_cols = list(key_cols)
    renamed = []
    for label, df in dfs.items():
        result_cols = [c for c in df.columns if c not in key_cols]
        renamed.append(df.rename(columns={c: f"{c}_{label}" for c in result_cols}))
    merged = reduce(lambda l, r: pd.merge(l, r, on=key_cols, how="outer"), renamed)

    result_names = set()
    for df in dfs.values():
        result_names.update(c for c in df.columns if c not in key_cols)
    for result in result_names:
        ts_cols = [c for c in merged.columns
                   if c.startswith(result + "_")
                   and not c.startswith("Binding_constraint")
                   and not c.startswith("Initial_kW")]
        merged[f"{result}_Min"] = merged[ts_cols].min(axis=1)
        merged[f"{result}_Max"] = merged[ts_cols].max(axis=1)
    return merged


class DynamicEVHostingCapacityResults:
    def __init__(self, merged_df, per_ts_results, output_dir):
        self._merged = merged_df
        self._per_ts = per_ts_results          # dict[label] -> EVHostingCapacityResults
        self._output_dir = Path(output_dir)

    def hosting_capacity_range(self) -> pd.DataFrame:
        return self._merged

    def summary(self) -> str:
        col_min, col_max = "Hosting_capacity_kW_Min", "Hosting_capacity_kW_Max"
        rng = self._merged[col_max] - self._merged[col_min]
        return "\n".join([
            f"Dynamic EV Hosting Capacity — {len(self._merged)} nodes, "
            f"{len(self._per_ts)} time points",
            f"  Median min HC: {self._merged[col_min].median():.0f} kW",
            f"  Median max HC: {self._merged[col_max].median():.0f} kW",
            f"  Median flexibility range: {rng.median():.0f} kW",
        ])

    def __repr__(self) -> str:
        return self.summary()
