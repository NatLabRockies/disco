# -*- coding: utf-8 -*-
"""Build a feeder model frozen at a specific time point, for Dynamic EV Hosting Capacity.

This module is used ONLY by the Dynamic HC path. It solves the feeder in Yearly mode
at a chosen hour to MEASURE the loadshape-resolved load powers, then writes a static
model (loadshapes stripped, kW/kvar baked to the hour-H values) that the existing
snapshot HC engine can run as-is. Normal (single-point) HC does not import this module.
"""

import os
import re
import opendssdirect as dss
import shutil
from pathlib import Path


def create_snapshot_loads(original_loads_file, output_loads_file, solved_loads):

    output_lines = []

    with open(original_loads_file, "r") as f:
        lines = f.readlines()

    for line in lines:

        line_out = line.rstrip()

        if "new load." not in line.lower():

            output_lines.append(line_out)
            continue

        match = re.search(r'new\s+load\.([^\s]+)', line, re.IGNORECASE)

        if not match:

            output_lines.append(line_out)
            continue

        load_name = match.group(1).lower()

        if load_name not in solved_loads:

            output_lines.append(line_out)
            continue

        kw = solved_loads[load_name]["kw"]
        kvar = solved_loads[load_name]["kvar"]

        line_out = re.sub(
            r'k[wW]=([0-9Ee\.\-\+]+)',
            f'kW={kw:.6f}',
            line_out
        )

        line_out = re.sub(
            r'kvar=([0-9Ee\.\-\+]+)',
            f'kvar={kvar:.6f}',
            line_out,
            flags=re.IGNORECASE
        )

        line_out = re.sub(
            r'\s*(yearly|daily|duty)=[^\s]+',
            '',
            line_out,
            flags=re.IGNORECASE
        )

        output_lines.append(line_out)

    with open(output_loads_file, "w") as f:

        for line in output_lines:
            f.write(line + "\n")


def get_solved_load_powers():

    load_dict = {}

    for load in dss.Loads.AllNames():

        dss.Circuit.SetActiveElement(f"Load.{load}")

        powers = dss.CktElement.Powers()

        kw = sum(powers[0::2])
        kvar = sum(powers[1::2])

        load_dict[load.lower()] = {
            "kw": abs(kw),
            "kvar": abs(kvar)
        }

    return load_dict


def create_snapshot_master(
        template_master,
        snapshot_master,
        new_loads_file,
        original_loads_file):
    """Write a per-hour master that points at the frozen loads file.

    The snapshot master lives in a different folder than the original feeder, so
    every other ``Redirect``/``Buscoords`` file reference is rewritten to an
    absolute path into the original feeder folder. The original loads redirect is
    replaced by ``new_loads_file`` (the frozen, loadshape-stripped loads that sit
    in the same folder as the snapshot master).
    """
    template_master = Path(template_master)
    base = template_master.parent
    original_loads_name = Path(original_loads_file).name.lower()

    output = []
    for raw in template_master.read_text().splitlines():
        stripped = raw.strip()

        # leave blank lines and comments untouched
        if not stripped or stripped.startswith("!"):
            output.append(raw)
            continue

        m = re.match(r'(redirect|buscoords)\s+(\S+\.dss)\s*(.*)$', stripped, re.IGNORECASE)
        if not m:
            output.append(raw)
            continue

        cmd, fname, rest = m.group(1), m.group(2), m.group(3)

        # the loads redirect -> point at the local frozen snapshot loads
        if cmd.lower() == "redirect" and Path(fname).name.lower() == original_loads_name:
            output.append(f'Redirect "{new_loads_file}"')
            continue

        # every other file reference -> absolute path into the original folder
        abs_path = (base / fname).resolve()
        tail = f' {rest}' if rest else ''
        output.append(f'{cmd} "{abs_path}"{tail}')

    Path(snapshot_master).write_text("\n".join(output) + "\n")


def datetime_to_dss_time(year, month, day, hour, minute):

    from datetime import datetime

    start = datetime(year, 1, 1)

    target = datetime(year, month, day, hour, minute)

    elapsed_hours = (target - start).total_seconds() / 3600

    return elapsed_hours


def _find_loads_file(master_dss):
    """Locate the .dss file (via Redirect) that actually defines the loads.

    Picks the first redirected file containing `New Load.` definitions, so it
    works regardless of filename (Loads.dss, Loads_with_loadshape.dss, etc.) and
    won't mistake the Loadshape.dss (which has `New Loadshape.`) for it.
    """
    master_dss = Path(master_dss)
    for raw in master_dss.read_text().splitlines():
        line = raw.strip()
        if line.startswith("!"):                       # skip commented-out redirects
            continue
        m = re.search(r'redirect\s+(\S+\.dss)', line, re.IGNORECASE)
        if not m:
            continue
        path = (master_dss.parent / m.group(1)).resolve()
        if path.exists() and re.search(r'new\s+load\.', path.read_text(), re.IGNORECASE):
            return path
    raise FileNotFoundError(
        f"No redirected .dss with 'New Load.' definitions found in {master_dss}"
    )


def build_dynamic_hc_model(master_dss, elapsed_hours, output_folder, label):
    """Freeze the feeder at ``elapsed_hours`` and return the per-hour master path.

    Solves in Yearly mode at the given elapsed hour to measure the loadshape-resolved
    load powers, then writes a static ``Loads_hour_<label>.dss`` (loadshapes stripped)
    plus a redirected ``Master_hour_<label>.dss`` into ``output_folder``.
    """
    master_dss = Path(master_dss)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    loads_dss = _find_loads_file(master_dss)

    # --- transient yearly solve to MEASURE loads at hour H ---
    dss.Basic.ClearAll()
    dss.Text.Command(f"Compile [{master_dss}]")
    dss.Text.Command("Set Mode=Yearly")
    dss.Text.Command(f"Set Hour={int(elapsed_hours)}")
    dss.Solution.Seconds(int((elapsed_hours % 1) * 3600))
    dss.Text.Command("Set Number=1")
    dss.Solution.Solve()
    solved_loads = get_solved_load_powers()

    # --- write frozen static loads + redirected master, then return master path ---
    snapshot_loads = output_folder / f"Loads_hour_{label}.dss"
    snapshot_master = output_folder / f"Master_hour_{label}.dss"
    create_snapshot_loads(loads_dss, snapshot_loads, solved_loads)
    create_snapshot_master(master_dss, snapshot_master, snapshot_loads.name, loads_dss)
    print(f"Created dynamic HC model for {label} (elapsed_hours={elapsed_hours})")
    return snapshot_master
