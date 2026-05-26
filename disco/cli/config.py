
import importlib

import click


_LAZY_SUBCOMMANDS = {
    "snapshot": ("disco.cli.config_snapshot", "snapshot"),
    "time-series": ("disco.cli.config_time_series", "time_series"),
    "upgrade": ("disco.cli.config_upgrade", "upgrade"),
}


class LazyConfigGroup(click.Group):
    """Click group that defers subcommand imports until the command is invoked."""

    def get_command(self, ctx, cmd_name):
        if cmd_name in _LAZY_SUBCOMMANDS:
            module_path, attr = _LAZY_SUBCOMMANDS[cmd_name]
            module = importlib.import_module(module_path)
            return getattr(module, attr)
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        eager = list(super().list_commands(ctx))
        return sorted(set(eager) | set(_LAZY_SUBCOMMANDS.keys()))


@click.group(cls=LazyConfigGroup)
def config():
    """Create JADE configurations for DISCO analysis types"""
