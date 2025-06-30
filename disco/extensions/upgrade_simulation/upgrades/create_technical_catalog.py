import os
import sys
import click
import glob
from pathlib import Path

from disco.extensions.upgrade_simulation.upgrades.common_functions import (
    get_thermal_equipment_info,
    reload_dss_circuit,
    ReloadCircuitParams,
    CircuitSolveParams,
    get_line_code,
    get_line_geometry,
    determine_available_line_upgrades,
    determine_available_xfmr_upgrades,
)
from disco.models.upgrade_cost_analysis_generic_input_model import UpgradeTechnicalCatalogModel
from jade.utils.utils import dump_data



def run(dss_file,output_path):

    internal_upgrades_technical_catalog_filepath = Path(output_path, 'upgrades_technical_catalog.json')

    solve_params = CircuitSolveParams()
    reload_circuit_params = ReloadCircuitParams()
    reload_dss_circuit(
        dss_file_list=[dss_file],
        commands_list=None,
        solve_params=solve_params,
        reload_circuit_params=reload_circuit_params,
            )


    upgrades_technical_catalog = {}
    orig_lines_df = get_thermal_equipment_info(compute_loading=False, equipment_type="line")
    orig_xfmrs_df = get_thermal_equipment_info(compute_loading=False, equipment_type="transformer")
    orig_linecode_df = get_line_code()
    orig_linegeometry_df = get_line_geometry()
    line_upgrade_options = determine_available_line_upgrades(orig_lines_df)
    xfmr_upgrade_options = determine_available_xfmr_upgrades(orig_xfmrs_df)
    upgrades_technical_catalog = {"line": line_upgrade_options.to_dict('records'), "transformer": xfmr_upgrade_options.to_dict('records'),
                                            "linecode": orig_linecode_df.to_dict('records'), 
                                            "geometry": orig_linegeometry_df.to_dict('records'),
                                            }
    # validate internal upgrades catalog
    input_catalog_model = UpgradeTechnicalCatalogModel(**upgrades_technical_catalog)
    dump_data(input_catalog_model.dict(by_alias=True), 
                internal_upgrades_technical_catalog_filepath, indent=2)  # write internal catalog to json
    


@click.command()
@click.argument("dss-file", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output-path",
    type=click.Path(),
    default="output",
    show_default=True,
    help="Output directory for results",
    callback=lambda _, __, z: Path(z),
)
def create_technical_catalog(dss_file, output_path, force):
    if output_path.exists() and not force:
        print(
            "%s already exists. Pass --force to overwrite or choose a custom name."
            % output_path
        )
        sys.exit(1)
    os.makedirs(output_path, exist_ok=True)

    run(dss_file, output_path)


if __name__ == "__main__":
    create_technical_catalog()

