# -*- coding: utf-8 -*-
"""Merge per-timestamp EV hosting-capacity tables into a Dynamic HC range result."""

from pathlib import Path
from functools import reduce

import matplotlib.pyplot as plt
import pandas as pd


def merge_timestamp_hosting_capacity(dfs: dict, key_cols) -> pd.DataFrame:
    """Build the final dynamic HC table from per-timestamp HC results.

    Keeps only the per-timestamp ``Hosting_capacity_kW`` values in the final
    dynamic table. Full per-timestamp details, such as initial load and binding
    constraint, remain available in each timestamp's EV HC result database.
    """
    key_cols = list(key_cols)
    renamed = []
    for label, df in dfs.items():
        keep_cols = key_cols + ["Hosting_capacity_kW"]
        missing = [c for c in keep_cols if c not in df.columns]
        if missing:
            raise ValueError(
                f"Timestamp {label!r} hosting_capacity table is missing columns: {missing}"
            )
        renamed.append(
            df[keep_cols].rename(
                columns={"Hosting_capacity_kW": f"Hosting_capacity_kW_{label}"}
            )
        )

    merged = reduce(lambda l, r: pd.merge(l, r, on=key_cols, how="outer"), renamed)

    ts_cols = [c for c in merged.columns if c.startswith("Hosting_capacity_kW_")]
    merged["Hosting_capacity_kW_Min"] = merged[ts_cols].min(axis=1)
    merged["Hosting_capacity_kW_Max"] = merged[ts_cols].max(axis=1)
    merged["Hosting_capacity_kW_Range"] = (
        merged["Hosting_capacity_kW_Max"] - merged["Hosting_capacity_kW_Min"]
    )
    return merged


class DynamicEVHostingCapacityResults:
    def __init__(self, merged_df, per_ts_results, output_dir):
        self._merged = merged_df
        self._per_ts = per_ts_results          # dict[label] -> EVHostingCapacityResults
        self._output_dir = Path(output_dir)

    def dynamic_hosting_capacity(self) -> pd.DataFrame:
        return self._merged

    def _dynamic_hc_plot_columns(self) -> list[str]:
        return [
            c for c in self._merged.columns
            if c.startswith("Hosting_capacity_kW_")
        ]

    def _dynamic_plot_data(self):
        if not self._per_ts:
            raise ValueError("No per-timestamp results are available to plot.")

        first_result = next(iter(self._per_ts.values()))
        coords = first_result.bus_coordinates()
        lines = first_result.line_segments()
        bus = coords.merge(self.dynamic_hosting_capacity(), on="Bus", how="left")
        return bus, lines

    def plot_dynamic_hosting_capacity_map(
        self,
        columns: list[str] | None = None,
        colorscale: str = "Turbo_r",
        width: int = 900,
        height: int = 650,
    ):
        """Plot dynamic EV HC as a branch map with a timestamp dropdown."""
        try:
            import plotly.graph_objects as go
            from plotly.colors import sample_colorscale
        except ImportError as exc:
            raise ImportError(
                "plot_dynamic_hosting_capacity_map requires plotly. "
                "Install it with `pip install plotly`."
            ) from exc

        bus, lines = self._dynamic_plot_data()
        columns = columns or self._dynamic_hc_plot_columns()
        if not columns:
            raise ValueError("No dynamic hosting-capacity columns are available to plot.")

        missing = [c for c in columns if c not in bus.columns]
        if missing:
            raise ValueError(f"Requested plot columns are missing: {missing}")

        xy = bus.set_index("Bus")
        values = bus[columns].to_numpy(dtype=float)
        finite = values[pd.notna(values)]
        if finite.size == 0:
            raise ValueError("No finite hosting-capacity values are available to plot.")

        cmin = float(finite.min())
        cmax = float(finite.max())
        if cmin == cmax:
            cmax = cmin + 1.0

        def branch_color(value):
            if pd.isna(value):
                return "rgba(180,180,180,0.45)"
            scaled = max(0.0, min(1.0, (float(value) - cmin) / (cmax - cmin)))
            return sample_colorscale(colorscale, scaled)[0]

        fig = go.Figure()
        trace_groups = []

        for col_index, column in enumerate(columns):
            visible = col_index == 0
            group_indices = []
            label = column.removeprefix("Hosting_capacity_kW_")

            for _, line in lines.iterrows():
                a, b = line["From_Bus"], line["To_Bus"]
                if a not in xy.index or b not in xy.index:
                    continue
                if pd.isna(xy.at[a, "X"]) or pd.isna(xy.at[a, "Y"]):
                    continue
                if pd.isna(xy.at[b, "X"]) or pd.isna(xy.at[b, "Y"]):
                    continue

                value = xy.at[b, column]
                fig.add_trace(go.Scatter(
                    x=[xy.at[a, "X"], xy.at[b, "X"]],
                    y=[xy.at[a, "Y"], xy.at[b, "Y"]],
                    mode="lines",
                    line=dict(color=branch_color(value), width=3),
                    hoverinfo="skip",
                    showlegend=False,
                    visible=visible,
                ))
                group_indices.append(len(fig.data) - 1)

            node_df = bus.dropna(subset=["X", "Y"])
            fig.add_trace(go.Scatter(
                x=node_df["X"],
                y=node_df["Y"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=node_df[column],
                    colorscale=colorscale,
                    cmin=cmin,
                    cmax=cmax,
                    colorbar=dict(title="EV HC (kW)"),
                    line=dict(color="black", width=0.5),
                ),
                text=node_df["Bus"],
                customdata=node_df[[column]],
                hovertemplate=(
                    "Bus: %{text}<br>"
                    + label
                    + ": %{customdata[0]:.2f} kW<extra></extra>"
                ),
                name=label,
                showlegend=False,
                visible=visible,
            ))
            group_indices.append(len(fig.data) - 1)
            trace_groups.append(group_indices)

        buttons = []
        for idx, column in enumerate(columns):
            visible = [False] * len(fig.data)
            for trace_idx in trace_groups[idx]:
                visible[trace_idx] = True

            label = column.removeprefix("Hosting_capacity_kW_")
            buttons.append(dict(
                label=label,
                method="update",
                args=[
                    {"visible": visible},
                    {"title": f"Dynamic EV Hosting Capacity - {label}"},
                ],
            ))

        initial_label = columns[0].removeprefix("Hosting_capacity_kW_")
        fig.update_layout(
            title=f"Dynamic EV Hosting Capacity - {initial_label}",
            width=width,
            height=height,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=130, b=20),
            updatemenus=[dict(
                buttons=buttons,
                direction="down",
                x=0.0,
                y=1.22,
                xanchor="left",
                yanchor="top",
            )],
        )
        return fig

    def plot_dynamic_hosting_capacity_by_distance(
        self,
        ax=None,
        max_labels: int = 20,
    ):
        """Plot min-to-max dynamic HC band by bus rank from the substation."""
        bus, _ = self._dynamic_plot_data()
        first_result = next(iter(self._per_ts.values()))
        dist = first_result.bus_distances()
        plot_df = bus[[
            "Bus",
            "Hosting_capacity_kW_Min",
            "Hosting_capacity_kW_Max",
        ]].merge(
            dist,
            on="Bus",
            how="left",
        )

        if "Distance" not in plot_df.columns:
            raise ValueError("bus_distances() must include a 'Distance' column.")

        plot_df = plot_df.dropna(
            subset=["Distance", "Hosting_capacity_kW_Min", "Hosting_capacity_kW_Max"]
        ).copy()
        plot_df = plot_df.sort_values("Distance").reset_index(drop=True)
        plot_df["Distance_rank"] = plot_df.index + 1
        if ax is None:
            _, ax = plt.subplots(figsize=(10, 4))

        ax.fill_between(
            plot_df["Distance_rank"],
            plot_df["Hosting_capacity_kW_Min"],
            plot_df["Hosting_capacity_kW_Max"],
            color="#4C78A8",
            alpha=0.5,
            label="Min-Max range",
        )
        ax.set_xlabel("Bus rank by distance from substation")
        ax.set_ylabel("Dynamic hosting capacity (kW)")
        ax.set_title("Dynamic EV HC by Distance")
        ax.grid(axis="y", alpha=0.3)
        if max_labels and len(plot_df) > 0:
            step = max(1, len(plot_df) // max_labels)
            ticks = plot_df["Distance_rank"].iloc[::step]
            labels = plot_df["Bus"].iloc[::step]
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, rotation=90)

        return ax

    def plot_dynamic_hosting_capacity_time_series_summary(self, ax=None):
        """Plot feeder-wide dynamic HC summary statistics over timestamps."""
        df = self.dynamic_hosting_capacity()
        timestamp_cols = [
            c for c in df.columns
            if c.startswith("Hosting_capacity_kW_")
            and not c.endswith(("_Min", "_Max", "_Range"))
        ]
        if not timestamp_cols:
            raise ValueError("No timestamp hosting-capacity columns are available to plot.")

        summary = pd.DataFrame({
            "timestamp": [c.removeprefix("Hosting_capacity_kW_") for c in timestamp_cols],
            "min": [df[c].min() for c in timestamp_cols],
            "p10": [df[c].quantile(0.10) for c in timestamp_cols],
            "median": [df[c].median() for c in timestamp_cols],
            "mean": [df[c].mean() for c in timestamp_cols],
            "p90": [df[c].quantile(0.90) for c in timestamp_cols],
            "max": [df[c].max() for c in timestamp_cols],
        })

        if ax is None:
            _, ax = plt.subplots(figsize=(10, 4))

        x = range(len(summary))
        ax.fill_between(x, summary["p10"], summary["p90"], alpha=0.25, label="10th-90th percentile")
        ax.plot(x, summary["median"], marker="o", label="Median")
        ax.plot(x, summary["mean"], marker="o", linestyle="--", label="Mean")
        ax.plot(x, summary["min"], linewidth=0.9, color="0.35", linestyle="--", label="Min")
        ax.plot(x, summary["max"], linewidth=0.9, color="0.35", label="Max")
        ax.set_xticks(list(x))
        ax.set_xticklabels(summary["timestamp"], rotation=45, ha="right")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Hosting capacity (kW)")
        ax.set_title("Dynamic EV HC Time Series Summary")
        ax.grid(axis="y", alpha=0.3)
        ax.legend(loc="best")

        return ax

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
