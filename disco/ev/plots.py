"""EV hosting capacity plots: density, contour, branch, nodal."""

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from scipy.interpolate import griddata

HC = "Hosting_capacity_kW"


class EVHostingCapacityPlots:
    def __init__(self, results):
        self._results = results
        # One row per bus with X, Y, and total hosting capacity.
        hc = results.hosting_capacity().groupby("Bus", as_index=False)[HC].sum()
        self.bus = results.bus_coordinates().merge(hc, on="Bus", how="left")
        self.lines = results.line_segments()

        valid = self.bus.dropna(subset=[HC])
        self.vmin = float(valid[HC].min())
        self.vmax = float(valid[HC].max())

    # ---- small helpers ------------------------------------------------------

    def _grid(self, resolution=300, method="linear"):
        """Interpolate bus HC onto a regular grid for density/contour."""
        df = self.bus.dropna(subset=[HC, "X", "Y"])
        x, y, z = df["X"].to_numpy(), df["Y"].to_numpy(), df[HC].to_numpy()
        gx, gy = np.mgrid[x.min():x.max():complex(0, resolution),
                          y.min():y.max():complex(0, resolution)]
        gz = griddata((x, y), z, (gx, gy), method=method)
        return df, gx, gy, gz

    def _draw_feeder(self, ax, color="0.78"):
        xy = self.bus.set_index("Bus")[["X", "Y"]]
        for _, line in self.lines.iterrows():
            a, b = line["From_Bus"], line["To_Bus"]
            if a in xy.index and b in xy.index:
                ax.plot([xy.at[a, "X"], xy.at[b, "X"]],
                        [xy.at[a, "Y"], xy.at[b, "Y"]],
                        color=color, linewidth=1.0, zorder=1)
                
    def _label_buses(self, ax, fontsize=8):
        df = self.bus.dropna(subset=["X", "Y"])
        for _, row in df.iterrows():
            ax.text(row["X"], row["Y"], str(row["Bus"]),
                    fontsize=fontsize, ha="left", va="bottom")

    def _finish(self, ax, mappable, title, save_path=None):
        plt.colorbar(mappable, ax=ax, label="EV hosting capacity (kW)")
        ax.set_title(title)
        ax.set_aspect("equal", adjustable="datalim")
        ax.axis("off")

        if save_path:
            ax.figure.savefig(save_path, dpi=200, bbox_inches="tight")

        return ax

    
    def _resolve_save_path(self, save, output_dir, filename):
        if not save:
            return None

        if save is True:
            out = Path(output_dir) if output_dir else self._results._output_dir
            save_path = out / filename
        else:
            save_path = Path(save)

        save_path.parent.mkdir(parents=True, exist_ok=True)
        return save_path

    # ---- plots --------------------------------------------------------------

    def density(self, ax=None, cmap="turbo", save=False, output_dir=None):
        """Interpolated EV hosting capacity heatmap (matches lindistflow style)."""
        df = self.bus.dropna(subset=[HC, "X", "Y"])
        x = df["X"].to_numpy()
        y = df["Y"].to_numpy()
        z = df[HC].to_numpy()

        grid_x, grid_y = np.mgrid[x.min():x.max():300j, y.min():y.max():300j]
        grid_z = griddata(points=(x, y), values=z, xi=(grid_x, grid_y), method="linear")

        if ax is None:
            _, ax = plt.subplots(figsize=(6, 5))

        self._draw_feeder(ax)

        heatmap = ax.imshow(
            grid_z.T,
            extent=(x.min(), x.max(), y.min(), y.max()),
            origin="lower",
            cmap=cmap,
            alpha=0.75,
            aspect="equal",
            interpolation="bicubic",
        )
        ax.figure.colorbar(heatmap, ax=ax, label="EV Hosting Capacity (kW)")

        all_buses = self.bus.dropna(subset=["X", "Y"])
        #ax.scatter(all_buses["X"], all_buses["Y"], c="black", s=25)
        #self._label_buses(ax)

        ax.set_title("EV Hosting Capacity - Density")
        ax.axis("equal")
        ax.axis("off")
        ax.figure.tight_layout()
        save_path = self._resolve_save_path(save, output_dir, "ev_hc_density.png")

        if save_path:
            ax.figure.savefig(save_path, dpi=200, bbox_inches="tight")
        return ax

    def contour(self, ax=None, levels=12, cmap="turbo", save=False, output_dir=None):
        df, gx, gy, gz = self._grid()
        if ax is None:
            _, ax = plt.subplots(figsize=(6, 5))
        cf = ax.contourf(gx, gy, gz,
                         levels=np.linspace(self.vmin, self.vmax, levels),
                         cmap=cmap, alpha=0.85)
        self._draw_feeder(ax, color="0.15")
        #ax.scatter(df["X"], df["Y"], s=18, c="black", zorder=3)
        #self._label_buses(ax)
        save_path = self._resolve_save_path(save, output_dir, "ev_hc_contour.png")
        return self._finish(ax, cf, "EV Hosting Capacity - Contour", save_path)

    def branch(self, ax=None, cmap="turbo", linewidth=3.0, save=False, output_dir=None):
        """Color each feeder line segment by the to-bus hosting capacity."""
        xy = self.bus.set_index("Bus")
        segments, values = [], []
        for _, line in self.lines.iterrows():
            a, b = line["From_Bus"], line["To_Bus"]
            if a in xy.index and b in xy.index and not np.isnan(xy.at[b, HC]):
                segments.append([(xy.at[a, "X"], xy.at[a, "Y"]),
                                 (xy.at[b, "X"], xy.at[b, "Y"])])
                values.append(xy.at[b, HC])

        if ax is None:
            _, ax = plt.subplots(figsize=(6, 5))
        self._draw_feeder(ax) 
        lc = LineCollection(segments, array=np.array(values), cmap=cmap,
                            linewidths=linewidth, clim=(self.vmin, self.vmax))
        ax.add_collection(lc)
        ax.autoscale_view()
        nodes = self.bus.dropna(subset=["X", "Y"])
        #ax.scatter(nodes["X"], nodes["Y"], s=14, c="black", zorder=3)
        #self._label_buses(ax)
        save_path = self._resolve_save_path(save, output_dir, "ev_hc_branch.png")
        return self._finish(ax, lc, "EV Hosting Capacity - Branch", save_path)

    def nodal(self, ax=None, cmap="turbo", size=42, save=False, output_dir=None):
        df = self.bus.dropna(subset=[HC, "X", "Y"])
        if ax is None:
            _, ax = plt.subplots(figsize=(6, 5))
        self._draw_feeder(ax, color="0.75")
        sc = ax.scatter(df["X"], df["Y"], c=df[HC], s=size, cmap=cmap,
                        vmin=self.vmin, vmax=self.vmax,
                        edgecolor="black", linewidth=0.35, zorder=2)
        #self._label_buses(ax)
        save_path = self._resolve_save_path(save, output_dir, "ev_hc_nodal.png")    
        return self._finish(ax, sc, "EV Hosting Capacity - Nodal", save_path)

    # ---- batch save ---------------------------------------------------------

    def all(self, save=False, output_dir=None):
        save_path = self._resolve_save_path(save, output_dir, "ev_hc_all.png")
        fig, axes = plt.subplots(2, 2, figsize=(14, 11))
        self.density(ax=axes[0, 0])
        self.contour(ax=axes[0, 1])
        self.branch(ax=axes[1, 0])
        self.nodal(ax=axes[1, 1])
        fig.suptitle(f"EV Hosting Capacity — {self._results._feeder_name}", fontsize=14)
        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=200, bbox_inches="tight")
        #return fig
