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

```bash
disco ev hosting-capacity path/to/Master.dss -o output/my_feeder
```

Run with the included example feeder (no feeder of your own needed):

```bash
disco ev hosting-capacity tests/data/generic-models/p1uhs21_1247/p1udt5257/OpenDSS/Master.dss -o output/ev_hc_example --overwrite --export-circuit-elements
```

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `-l, --lower-voltage-limit` | `0.95` | Lower voltage limit (P.U.) |
| `-u, --upper-voltage-limit` | `1.05` | Upper voltage limit (P.U.) |
| `-v, --kw-step-voltage-violation` | `10.0` | kW step for voltage bisection search |
| `-t, --kw-step-thermal-violation` | `10.0` | kW step for thermal bisection search |
| `--voltage-tolerance` | same as `-v` | Convergence tolerance for voltage search |
| `--thermal-tolerance` | same as `-t` | Convergence tolerance for thermal search |
| `-T, --thermal-loading-limit` | `100.0` | Max thermal loading (%) |
| `-e, --extra-percentage-for-existing-overloads` | `2.0` | Extra headroom for pre-overloaded elements |
| `-c, --num-cpus` | all CPUs | Parallel workers |
| `--export-circuit-elements` | off | Export rated values for all circuit elements |
| `-o, --output` | `output` | Output directory |
| `--overwrite` | off | Overwrite existing output directory |
| `--verbose` | off | Enable debug logging |

## Output Files

All files are written to the output directory.

### `Hosting_capacity_voltage_test_<lower>_<upper>.csv`
Per-load voltage hosting capacity.

| Column | Description |
|--------|-------------|
| `Load` | OpenDSS load name |
| `Bus` | Bus the load is connected to |
| `Initial_kW` | Baseline load (kW) |
| `Volt_Violation` | Max kW that triggers a voltage violation |
| `Maximum_kW` | Hosting capacity limited by voltage (kW) |
| `Max_voltage` | Highest bus voltage seen during search (P.U.) |
| `Min_voltage` | Lowest bus voltage seen during search (P.U.) |

### `Hosting_capacity_thermal_test_<limit>.csv`
Per-load thermal hosting capacity.

| Column | Description |
|--------|-------------|
| `Load` | OpenDSS load name |
| `Bus` | Bus the load is connected to |
| `Initial_kW` | Baseline load (kW) |
| `Thermal_Violation` | Min kW that causes a thermal violation |
| `Maximum_kW` | Hosting capacity limited by thermal loading (kW) |

### `Additional_HostingCapacity_<limit>.csv`
Extra EV load each node can absorb beyond its current load.

| Column | Description |
|--------|-------------|
| `Load` | OpenDSS load name |
| `Bus` | Bus the load is connected to |
| `Initial_kW` | Baseline load (kW) |
| `Hosting_capacity(kW)` | Additional kW available (Maximum_kW − Initial_kW) |

### `Loadwithlevel3_2_1_<limit>.csv`
Number of EV chargers assignable per load based on additional hosting capacity.

| Column | Description |
|--------|-------------|
| `load` | OpenDSS load name |
| `bus` | Bus the load is connected to |
| `no. of level3` | Level 3 / XFC chargers (350 kW each) |
| `no. of level2` | Level 2 chargers (7.2 kW each) |
| `no. of level1` | Level 1 chargers (3.3 kW each) |

### `node_distance.csv`
Distance of each bus from the substation (used for spatial plots).

### `Cap_by_V_limit.png` / `Cap_by_thermal_limit_<limit>.png`
Scatter plots of hosting capacity vs. distance from substation, for voltage and thermal constraints respectively.

### `circuit_elements/` (with `--export-circuit-elements`)
One CSV per element type (Line, Transformer, Load, etc.) with rated properties from OpenDSS.

## Algorithm

This tool computes **nodal hosting capacity** — for each load node individually, it finds
the maximum EV charging load that node can absorb before any voltage or thermal limit is
violated anywhere in the feeder. Each node is tested in isolation (one at a time), so the
results represent the headroom at each connection point independently, not the capacity
when all nodes charge simultaneously (system-level HC).

The tool runs two independent binary searches (bisection) per load node:

**Voltage search:** Starting at 2× the current load kW, the tool doubles the load until a
voltage violation occurs (any bus outside `[lower_limit, upper_limit]`), then bisects
between the last passing value and the first violating value until convergence.

**Thermal search:** Same approach, but the violation condition is any line or transformer
exceeding `thermal_loading_limit` (default 100%).

Both searches run in parallel across all load nodes using Python `ProcessPoolExecutor`.

> **Note:** Because each node is tested independently, the results are optimistic —
> they represent the maximum each node could absorb on its own. In reality, if multiple
> nodes charge simultaneously, the combined stress on the network would reduce the actual
> capacity available at each node.

## Charger Level Assignment

Given the additional hosting capacity (kW) at each node, chargers are assigned greedily:

1. As many **Level 3 (XFC)** chargers as fit at 350 kW each
2. Remaining kW filled with **Level 2** at 7.2 kW each
3. Any remainder filled with **Level 1** at 3.3 kW each

Example: 500 kW available → 1× L3 (350 kW) + 20× L2 (144 kW) + 1× L1 (3.3 kW)
