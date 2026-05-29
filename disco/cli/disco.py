"""Main CLI command for disco."""

import importlib
import logging
from pathlib import Path

import click

from jade.utils.subprocess_manager import check_run_command

import disco

logger = logging.getLogger(__name__)


# Subcommands are loaded lazily so that missing optional dependencies (e.g. PyDSS)
# only cause errors when the affected subcommand is actually invoked.
_LAZY_COMMANDS = {
    "config": ("disco.cli.config", "config"),
    "config-generic-models": ("disco.cli.config_generic_models", "config_generic_models"),
    "simulation-models": ("disco.cli.simulation_models", "simulation_models"),
    "download-source": ("disco.cli.download_source", "download_source"),
    "transform-model": ("disco.cli.transform_model", "transform_model"),
    "prescreen-pv-penetration-levels": ("disco.cli.prescreen_pv_penetration_levels", "prescreen_pv_penetration_levels"),
    "pv-deployments": ("disco.cli.pv_deployments", "pv_deployments"),
    "create-pipeline": ("disco.cli.create_pipeline", "create_pipeline"),
    "ingest-tables": ("disco.cli.ingest_tables", "ingest_tables"),
    "make-summary-tables": ("disco.cli.make_summary_tables", "make_summary_tables"),
    "compute-hosting-capacity": ("disco.cli.compute_hosting_capacity", "compute_hosting_capacity"),
    "plot": ("disco.cli.plots", "plot"),
    "summarize-hosting-capacity": ("disco.cli.summarize_hosting_capacity", "summarize_hosting_capacity"),
    "upgrade-cost-analysis": ("disco.cli.upgrade_cost_analysis", "upgrade_cost_analysis"),
    "hosting-capacity-by-timestep": ("disco.cli.pydss_hosting_capacity", "hosting_capacity_by_timestep"),
}


class LazyGroup(click.Group):
    """Click group that defers subcommand imports until the command is invoked."""

    def get_command(self, ctx, cmd_name):
        if cmd_name in _LAZY_COMMANDS:
            module_path, attr = _LAZY_COMMANDS[cmd_name]
            module = importlib.import_module(module_path)
            return getattr(module, attr)
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        eager = list(super().list_commands(ctx))
        return sorted(set(eager) | set(_LAZY_COMMANDS.keys()))


@click.command()
def install_extensions():
    """Install DISCO's JADE extensions."""
    ext_path = Path(disco.__path__[0]) / "extensions" / "jade_extensions.json"
    check_run_command(f"jade extensions register {ext_path}")


@click.group(cls=LazyGroup)
def cli():
    """Entry point"""


cli.add_command(install_extensions)
