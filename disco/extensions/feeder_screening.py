import os
import sys
import click
import networkx as nx
import pandas as pd
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from disco.extensions.upgrade_simulation.upgrades.common_functions import get_snapshot_transformer_info, get_snapshot_line_info, get_snapshot_bus_voltage_violations, \
    reload_dss_circuit, ReloadCircuitParams, CircuitSolveParams, get_circuit_info, get_dss_object_counts, get_feeder_stats
from disco.extensions.upgrade_simulation.upgrades.voltage_upgrade_functions import plot_feeder, generate_networkx_representation, get_bus_coordinates
# from jade.utils.timing_utils import track_timing, Timer
from jade.utils.utils import dump_data, load_data


# class AnalysisParamsBaseModel(BaseModel):
#     """Base model for all upgrade cost analysis parameters"""

#     class Config:
#         title = "UpgradeParamsBaseModel"
#         anystr_strip_whitespace = True
#         validate_assignment = True
#         validate_all = True
#         extra = "forbid"
#         use_enum_values = False
#         arbitrary_types_allowed = True

#     @classmethod
#     def from_file(cls, filename: Path):
#         """Return an instance from a file

#         Parameters
#         ----------
#         filename : Path

#         """
#         return cls(**load_data(filename))
    

# class FeederOutputParams(AnalysisParamsBaseModel):
    


# @track_timing(timer_stats_collector)
def run(dss_file, config, output_path, render_plot=True, fmt="csv"):
    summary_filepath = os.path.join(output_path, "summary")
    xfmr_filepath = os.path.join(output_path, "transformer")
    line_filepath = os.path.join(output_path, "line")
    voltage_filepath = os.path.join(output_path, "voltage")
    bus_filepath = os.path.join(output_path, "bus_coordinates")

    xfmr_fields = ["name", "phases", "kV", "kVs", "kVA", "amp_limit_per_phase", "max_per_unit_loading", "status", "bus_names_only"]
    line_fields = ["name", "length", "phases", "kV", "h", "normamps", "max_per_unit_loading", "status"]
    voltage_fields = ['name', 'voltages', 'max_per_unit_voltage', 'min_per_unit_voltage',
       'phase_imbalance', 'overvoltage_violation', 'undervoltage_violation']

    try: 

        solve_params = CircuitSolveParams()
        reload_circuit_params = ReloadCircuitParams()
        reload_dss_circuit(dss_file_list=[dss_file], commands_list=None, solve_params=solve_params, reload_circuit_params=reload_circuit_params)

        xfmr_df = get_snapshot_transformer_info(upper_limit=config["xfmr_upper_limit"], compute_loading=True)
        line_df = get_snapshot_line_info(upper_limit=config["line_upper_limit"], compute_loading=True, ignore_switch=True)
        bus_voltages_df, undervoltage_bus_list, overvoltage_bus_list, buses_with_violations = get_snapshot_bus_voltage_violations(
                    voltage_upper_limit=config["voltage_upper_limit"], voltage_lower_limit=config["voltage_lower_limit"], solve_params=solve_params)

        orig_ckt_info = get_circuit_info()
        G = generate_networkx_representation()
        bus_dict = nx.get_node_attributes(G, 'pos')
        # bus_coordinates_df = get_bus_coordinates()
        connectivity_status = nx.is_connected(G.to_undirected())
        isolated = list(nx.isolates(G))
        
        if line_df.empty:
            num_line_overloads = 0
            max_line_loading = None
            num_unloaded_lines = 0
        else:
            num_line_overloads = len(line_df.loc[line_df.status=="overloaded"])
            max_line_loading = line_df.max_per_unit_loading.max()
            num_unloaded_lines =  len(line_df.loc[line_df.status=="unloaded"])

        summary_dict = {'num_overvoltages': len(overvoltage_bus_list), 'max_voltage': bus_voltages_df.max_per_unit_voltage.max(),
                        'num_undervoltages': len(undervoltage_bus_list), 'min_voltage': bus_voltages_df.min_per_unit_voltage.min(),
                        'num_line_overloads': num_line_overloads, 'max_line_loading': max_line_loading,
                        'num_xfmr_overloads': len(xfmr_df.loc[xfmr_df.status=="overloaded"]), 'max_xfmr_overload': xfmr_df.max_per_unit_loading.max(),
                        'num_unloaded_xfmrs': len(xfmr_df.loc[xfmr_df.status=="unloaded"]),
                        'num_unloaded_lines': num_unloaded_lines,
                        'connectivity_flag': connectivity_status, 'isolated': isolated}
        
        summary_dict.update(get_dss_object_counts())
        summary_dict.update(orig_ckt_info)
        summary_dict.update(get_feeder_stats())
        
        ov_flag = summary_dict["num_overvoltages"] > 0
        uv_flag = summary_dict["num_undervoltages"] > 0
        lo_flag = summary_dict["num_line_overloads"] > 0
        xo_flag = summary_dict["num_xfmr_overloads"] > 0
        
        summary_dict["pass_flag"] = (not ov_flag) and (not uv_flag) and (not lo_flag) and (not xo_flag) and (not connectivity_status)
        
        if render_plot:
            plot_feeder(fig_folder=output_path, title="Feeder circuit plot", circuit_source=orig_ckt_info['source_bus'], enable_detailed=True)
        
        summary_dict
        if fmt == "csv":
            bus_df = pd.DataFrame(bus_dict).T.reset_index().rename(columns={0:"x_coordinate", 1: "y_coordinate", "index": "bus_name"})
            bus_df.to_csv(bus_filepath+".csv")
            
            summary_df = pd.DataFrame(list(summary_dict.items())).rename(columns={0:"parameter", 1: "value"})
            summary_df.to_csv(summary_filepath+".csv")
            
            if not line_df.empty:
                line_df[line_fields].to_csv(line_filepath+".csv")
                
            xfmr_df[xfmr_fields].to_csv(xfmr_filepath+".csv")
            bus_voltages_df[voltage_fields].to_csv(voltage_filepath+".csv")
            
        elif fmt == "json":
            all_dict = {"summary": summary_dict, "transformer": xfmr_df[xfmr_fields].to_dict("records"), 
                        "voltage": bus_voltages_df[voltage_fields].to_dict("records"), "bus_coordinates": bus_dict}
            if not line_df.empty:
                all_dict["line"] = xfmr_df[xfmr_fields].to_dict("records")
                
            dump_data(all_dict, summary_filepath+".json", indent=2)
            
    except Exception as e:
        print(e)

    return


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
@click.option(
    "--render-plot",
    is_flag=True,
    default=True,
    show_default=True,
    help="Render and save circuit plot",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    show_default=True,
    help="Overwrite output directory if it already exists.",
)
@click.option(
    "--fmt",
    type=str,
    default="csv",
    show_default=True,
    help="Format for saving output file.",
)
@click.option(
    "--config",
    type=dict,
    default={"xfmr_upper_limit": 1.0, "line_upper_limit": 1.0, "voltage_upper_limit": 1.05, "voltage_lower_limit": 0.95},
    show_default=True,
    help="Configuration parameters",
)
def snapshot_summary(dss_file, config, output_path, render_plot, fmt, force):    
    # level = logging.DEBUG if verbose else logging.INFO
    # setup_logging(LOGGER_NAME, None, console_level=level, packages=["disco"])

    # render_plot = True
    # job_name = "test"
    # config = {"xfmr_upper_limit": 1.0, "line_upper_limit": 1.0, "voltage_upper_limit": 1.05, "voltage_lower_limit": 0.95}
    
    # feeder_path = r"C:\Users\SABRAHAM\Documents\GitHub\Tools\disco\tests\data\upgrade-models\uo_baseline_scenario_undersized2\opendss\dss_files"
    # feeder_path = r"C:\Users\SABRAHAM\Documents\GitHub\Tools\disco\tests\data\upgrade-models\sb10_p7uhs7_1247_trans_301\p7udt173\PVDeployments"
    # feeder_path = r"C:\Users\SABRAHAM\Desktop\NREL\current_projects\LA100ES\feeder_models\B\14\14_06"
    # feeder_path = r"C:\Users\SABRAHAM\Desktop\NREL\current_projects\LA100ES\1_01"
    
    # dss_file = os.path.join(feeder_path, "Original_Master.dss")
    # dss_file = os.path.join(feeder_path, "sb10_p7uhs7_1247_trans_301__p7udt173__random__7__85.dss")

    # output_path = os.path.join(feeder_path, "feeder_screening")
    if output_path.exists() and not force:
        print(
            "%s already exists. Pass --force to overwrite or choose a custom name." %output_path
        )
        sys.exit(1)
    os.makedirs(output_path, exist_ok=True)
    
    run(dss_file, config, output_path, render_plot, fmt)
    # run(dss_file, config, render_plot=render_plot, output_format="json")


if __name__ == '__main__':
    snapshot_summary()