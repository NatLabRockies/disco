# EV Hosting Capacity

DISCO computes the maximum amount of EV charging load a distribution feeder can absorb
before violating voltage or thermal limits, using OpenDSS power flow simulations.

## Installation

```bash
git clone <repo>
cd disco
pip install -e .
```

## Quick Start

The Python API is built around three classes: `Feeder`, `EVHostingCapacity`, and
`EVHostingCapacityResults`.

```python
import disco
from pathlib import Path

master = Path(r"C:\path\to\IEEE123Master.dss")
output_dir = Path(r"C:\path\to\output_EV_hosting_capacity\123Bus")

feeder = disco.Feeder.from_opendss(master)
results = disco.EVHostingCapacity(feeder=feeder, num_cpus=12).run(output_dir=output_dir)

print(results)             # uses __repr__ → summary()
```

Example output:

```
EV Hosting Capacity Summary — 123Bus Feeder
===========================================
Nodes analyzed:      92
Voltage-limited:     92 nodes
Thermal-limited:     0 nodes
Median capacity:     0 kW
Mean capacity:       10869 kW
Min capacity:        0 kW
Max capacity:        999990 kW
```

> **Reading the summary** — `Median: 0 kW` means a large share of nodes already violate
> voltage at their current load (the bisection hit its lower bound). `Max: 999990 kW` is
> the bisector's `UPPER_CAP` sentinel: those nodes never triggered a violation even at
> the cap, so their "real" capacity is unbounded by this analysis.

### Loading a past run without re-simulating

```python
from disco.ev.results import EVHostingCapacityResults

results = EVHostingCapacityResults.from_db(output_dir)
print(results.summary())
```

This reads everything back from `output_dir/disco_ev_hc.db`. Useful when iterating on
analysis without paying the simulation cost again.

## The Three Classes

### `disco.Feeder`

Represents a feeder loaded from an OpenDSS master file.

| Method / Attribute | Returns | Notes |
|---|---|---|
| `Feeder.from_opendss(master_path)` | `Feeder` | Classmethod constructor |
| `feeder.master_file` | `Path` | Path to `Master.dss` |
| `feeder.name` | `str` | Derived from the OpenDSS circuit name |
| `feeder.validate()` | `None` | Raises if the master file can't be compiled |

### `disco.EVHostingCapacity`

The simulation runner.

| Method / Attribute | Returns | Notes |
|---|---|---|
| `EVHostingCapacity(feeder, num_cpus=None)` | instance | `num_cpus=None` → uses `os.cpu_count()` |
| `.run(output_dir)` | `EVHostingCapacityResults` | Runs voltage + thermal bisections in parallel; writes to SQLite |

### `disco.ev.results.EVHostingCapacityResults`

Results container. Methods either compute on in-memory DataFrames or read from
the run's SQLite DB (lazy, queried each call).

| Method | Returns | Source |
|---|---|---|
| `summary()` | `str` | computed |
| `hosting_capacity()` | `DataFrame` | computed; combines voltage + thermal, includes `Binding_constraint` |
| `voltage_screen()` | `DataFrame` | SQLite table `voltage_screen` |
| `thermal_screen()` | `DataFrame` | SQLite table `thermal_screen` |
| `additional_capacity()` | `DataFrame` | SQLite table `additional_capacity` (legacy diagnostic, thermal-only) |
| `chargers()` | `DataFrame` | SQLite table `chargers` |
| `bus_distances()` | `DataFrame` | SQLite table `bus_distances` |
| `simulation_metadata()` | `dict[str, str]` | SQLite table `simulation_metadata` |
| `db_path` *(property)* | `Path` | Path to `disco_ev_hc.db` |
| `EVHostingCapacityResults.from_db(output_dir)` *(classmethod)* | instance | Reload past run from disk |

The two computed methods (`summary`, `hosting_capacity`) are the authoritative answer.
The table readers expose raw inputs for ad-hoc analysis.

## Output

A successful run produces a single self-contained file:

```
output_dir/
└── disco_ev_hc.db        # SQLite database — all tables below
```

Open it with any SQLite viewer (DB Browser for SQLite, VS Code's SQLite extension,
the `sqlite3` CLI) or read tables back via `EVHostingCapacityResults` methods.

### `voltage_screen`
Per-load voltage hosting capacity. Read via `results.voltage_screen()`.

| Column | Description |
|--------|-------------|
| `Load` | OpenDSS load name |
| `Bus` | Bus the load is connected to |
| `Initial_kW` | Baseline load (kW) |
| `Volt_Violation` | First kW (during search) that triggered a voltage violation |
| `Maximum_kW` | Highest kW that *passed* (no violation) |
| `Max_voltage` | Highest bus voltage seen during search (P.U.) |
| `Min_voltage` | Lowest bus voltage seen during search (P.U.) |

### `thermal_screen`
Per-load thermal hosting capacity. Read via `results.thermal_screen()`.

| Column | Description |
|--------|-------------|
| `Load` | OpenDSS load name |
| `Bus` | Bus the load is connected to |
| `Initial_kW` | Baseline load (kW) |
| `Thermal_Violation` | First kW (during search) that triggered a thermal violation |
| `Maximum_kW` | Highest kW that *passed* |

### `additional_capacity`
Legacy diagnostic — additional EV load each node can absorb beyond its current load,
computed *thermal-only* as `Thermal_Violation − Initial_kW`. For the
voltage-and-thermal-aware answer, use `results.hosting_capacity()` instead.

| Column | Description |
|--------|-------------|
| `Load` | OpenDSS load name |
| `Bus` | Bus the load is connected to |
| `Initial_kW` | Baseline load (kW) |
| `Hosting_capacity(kW)` | Additional kW (thermal only) |

### `chargers`
Number of EV chargers assignable per load based on additional hosting capacity.

| Column | Description |
|--------|-------------|
| `load` | OpenDSS load name |
| `bus` | Bus the load is connected to |
| `no. of level3` | Level 3 / XFC chargers (350 kW each) |
| `no. of level2` | Level 2 chargers (7.2 kW each) |
| `no. of level1` | Level 1 chargers (3.3 kW each) |

### `bus_distances`
Distance of each bus from the substation (used for spatial plots).

| Column | Description |
|--------|-------------|
| `node` | Node name (e.g. `bus123.1`) |
| `distance` | Path distance from substation (in feeder units) |

### `simulation_metadata`
Run configuration as key/value rows. Read as a dict via `results.simulation_metadata()`.

Currently records: `feeder_name`, `lower_voltage_limit`, `upper_voltage_limit`,
`thermal_loading_limit`, `run_timestamp`. Schema is open — adding a field requires no
migration, just pass another kwarg at the call site.

### Computed: `hosting_capacity()`

The recommended per-load answer. Combines voltage and thermal screens. Not a stored
table — built on the fly from `voltage_screen` and `thermal_screen`.

| Column | Description |
|--------|-------------|
| `Load` | OpenDSS load name |
| `Bus` | Bus the load is connected to |
| `Initial_kW` | Baseline load (kW) |
| `Hosting_capacity_kW` | Additional kW = `min(Vmax, Thmax) − Initial_kW`, floored at 0 |
| `Binding_constraint` | `"voltage"` or `"thermal"` — which limit was binding |

## Algorithm

This tool computes **nodal hosting capacity** — for each load node individually, it finds
the maximum EV charging load that node can absorb before any voltage or thermal limit is
violated anywhere in the feeder. Each node is tested in isolation, so the results
represent the headroom at each connection point independently, not the capacity when all
nodes charge simultaneously (system-level HC).

The tool runs two independent binary searches (bisection) per load node:

**Voltage search:** Starting at 2× the current load kW, the tool doubles the load until a
voltage violation occurs (any bus outside `[lower_limit, upper_limit]`), then bisects
between the last passing value and the first violating value until convergence.

**Thermal search:** Same approach, but the violation condition is any line or transformer
exceeding `thermal_loading_limit` (default 100%).

Both searches run in parallel across all load nodes using Python `ProcessPoolExecutor`.

### Edge cases handled by the bisector

- **OpenDSS solver non-convergence** is treated as a violation (the bisector backs off
  rather than diverging at extreme kW).
- **No violation reachable** — the bisector caps `cur_value` at
  `ViolationBisector.UPPER_CAP = 1_000_000.0` kW. Nodes that hit the cap appear in the
  output with `Maximum_kW ≈ 1_000_000` and should be interpreted as *"no realistic
  voltage/thermal limit found within this feeder"* — not as 1 GW of literal capacity.
- **Already-overloaded loads** report a hosting capacity of 0 kW (clamped) rather than a
  negative number.

> **Interpretation note:** Because each node is tested independently, the results are
> optimistic — they represent the maximum each node could absorb on its own. In reality,
> if multiple nodes charge simultaneously, the combined stress on the network would reduce
> the actual capacity available at each node.

## Charger Level Assignment

Given the additional hosting capacity (kW) at each node, chargers are assigned greedily:

1. As many **Level 3 (XFC)** chargers as fit at 350 kW each
2. Remaining kW filled with **Level 2** at 7.2 kW each
3. Any remainder filled with **Level 1** at 3.3 kW each

Example: 500 kW available → 1× L3 (350 kW) + 20× L2 (144 kW) + 1× L1 (3.3 kW)

## Tips and Gotchas

- **Default `num_cpus`** is `os.cpu_count()` — typically all logical cores. On a shared
  workstation, leave 1–2 cores free (`num_cpus=os.cpu_count() - 2`).
- **Each worker re-compiles OpenDSS** at the start of every load. For feeders with very
  few loads (<30), the spawn overhead can dominate — try `num_cpus=4` first.
- **Master.dss is mutated in place** during a run (solve directives stripped, replaced
  with `Solve mode=snapshot`), then restored from a `.bk` backup in a `finally:` block.
  The restore is robust to crashes; if you ever do see a stranded `.bk`, the original
  file content is in there.
- **Logging level** — `disco.ev` is set to `WARNING` by default. To see per-run progress
  info, raise it in your notebook:
  ```python
  import logging
  logging.basicConfig(level=logging.INFO, force=True)
  logging.getLogger("disco.ev").setLevel(logging.INFO)
  ```
- **`results.summary()` returns a string.** Print it directly (`print(results.summary())`)
  for nice multi-line rendering. The bare `results` shortcut also works because `__repr__`
  delegates to `summary()`. Calling `results.summary()` *as the last line of a cell*
  shows the escaped repr (`'EV Hosting...\\n========\\n...'`) — that's standard Python
  string display, not a bug.
