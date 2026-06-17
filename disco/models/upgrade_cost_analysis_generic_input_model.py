import typing
from typing import List, Optional, Set, Dict
from pydantic import Field, field_validator, model_validator, ConfigDict
from pydantic import ValidationError

import pandas as pd

from pydss.controllers import PvControllerModel

from disco.models.base import BaseAnalysisModel
from disco.models.upgrade_cost_analysis_equipment_model import *
from disco.extensions.upgrade_simulation.upgrade_configuration import DEFAULT_UPGRADE_PARAMS_FILE

_DEFAULT_UPGRADE_PARAMS = None
_SUPPORTED_UPGRADE_TYPES = ["thermal", "voltage"]


def _get_default_upgrade_params():
    global _DEFAULT_UPGRADE_PARAMS
    if _DEFAULT_UPGRADE_PARAMS is None:
        _DEFAULT_UPGRADE_PARAMS = load_data(DEFAULT_UPGRADE_PARAMS_FILE)
    return _DEFAULT_UPGRADE_PARAMS


def _json_schema_type(annotation):
    """Map a pydantic field annotation to its JSON-schema "type" string.

    Optional/Union-with-None annotations are unwrapped to their inner type so that,
    e.g., ``Optional[float]`` maps to ``"number"`` (matching pydantic v1 behavior).
    Returns ``None`` for ``Any`` or otherwise untyped annotations.
    """
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return _json_schema_type(args[0])
        return None
    if origin in (list, set, tuple):
        return "array"
    if origin is dict:
        return "object"
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "integer"
    if annotation is float:
        return "number"
    if annotation is str:
        return "string"
    return None


def _extract_specific_model_properties_(model_name, field_type_key, field_type_value):
    """Return the (alias) names of fields whose schema metadata matches the given key/value.

    ``field_type_key="type"`` matches against the field's JSON-schema type; any other key is
    matched against the field's ``json_schema_extra`` metadata (custom Field kwargs such as
    ``determine_upgrade_option``). Names are returned using their alias when one is defined, to
    match the by-alias schema used previously.
    """
    result = []
    for name, field in model_name.model_fields.items():
        key = field.alias or name
        if field_type_key == "type":
            if _json_schema_type(field.annotation) == field_type_value:
                result.append(key)
        else:
            extra = field.json_schema_extra or {}
            if extra.get(field_type_key) == field_type_value:
                result.append(key)
    return result


def get_default_thermal_upgrade_params():
    return _get_default_upgrade_params()["thermal_upgrade_params"]


def get_default_voltage_upgrade_params():
    return _get_default_upgrade_params()["voltage_upgrade_params"]


class OpenDSSLineModel(OpenDSSLineParams):
    bus1: str = Field(
        title="bus1",
        description="bus1",
    )
    bus2: str = Field(
        title="bus2",
        description="bus2",
    )
    length: float = Field(
        title="length",
        description="length",
    )
    enabled: Any = Field(
        default=None,
        title="enabled",
        description="enabled",
    )


class LineModel(OpenDSSLineModel, ExtraLineParams):
    name: str = Field(
        title="name",
        description="name. This is not a direct OpenDSS object property.",
    )


class LineCatalogModel(OpenDSSLineParams, ExtraLineParams):
    """Contains Line information needed for thermal upgrade analysis. Most fields can be directly obtained from the opendss models"""
    name: str = Field(
        title="name",
        description="name. This is not a direct OpenDSS object property.",
    )


class LineCodeCatalogModel(CommonLineParameters):
    """Contains LineCode information needed for thermal upgrade analysis. Most fields can be directly obtained from the opendss models"""
    name: str = Field(
        title="name",
        description="name",
    )
    nphases: int = Field(
        title="nphases",
        description="nphases",
        determine_upgrade_option=True,
    )
    Kron: Optional[Any] = Field(
        title="Kron",
        description="Kron",
        default="N",
        determine_upgrade_option=True,
    )
    neutral: float = Field(
        title="neutral",
        description="neutral",
        determine_upgrade_option=True,
    )
    like: Optional[Any] = Field(
        title="like",
        description="like",
        default=None,
    )
    baseFreq: float = Field(
        title="basefreq",
        description="basefreq",
        determine_upgrade_option=True,
    )
    

class LineGeometryCatalogModel(UpgradeParamsBaseModel):
    """Contains LineGeometry information needed for thermal upgrade analysis. Most fields can be directly obtained from the opendss models"""
    name: str = Field(
        title="name",
        description="name",
    )
    equipment_type: str = Field(
        title="equipment_type",
        description="equipment_type",
        determine_upgrade_option=True,
    )
    nconds: int = Field(
        title="nconds",
        description="nconds",
        determine_upgrade_option=True,
    )
    nphases: int = Field(
        title="nphases",
        description="nphases",
        determine_upgrade_option=True,
    )
    cond: int = Field(
        title="cond",
        description="cond",
        determine_upgrade_option=True,
    )
    wire: str = Field(
        title="wire",
        description="wire",
        determine_upgrade_option=True,
    )
    x: List[float] = Field(
        title="x",
        description="x",
        determine_upgrade_option=True,
    )
    h: List[float] = Field(
        title="h",
        description="h",
        determine_upgrade_option=True,
    )
    units: List[str] = Field(
        title="units",
        description="units",
        determine_upgrade_option=True,
    )
    normamps: float = Field(
        title="normamps",
        description="normamps",
        determine_upgrade_option=True,
    )
    emergamps: float = Field(
        title="emergamps",
        description="emergamps",
        determine_upgrade_option=True,
    )
    reduce: str = Field(
        title="reduce",
        description="reduce",
        determine_upgrade_option=True,
    )
    spacing: Optional[Any] = Field(
        default=None,
        title="spacing",
        description="spacing",
    )
    wires: List[str] = Field(
        title="wires",
        description="wires",
        determine_upgrade_option=True,
    )
    cncable: str = Field(
        title="cncable",
        description="cncable",
        determine_upgrade_option=True,
    )
    tscable: str = Field(
        title="tscable",
        description="tscable",
        determine_upgrade_option=True,
    )
    cncables: List[str] = Field(
        title="cncables",
        description="cncables",
        determine_upgrade_option=True,
    )
    tscables: List[str] = Field(
        title="tscables",
        description="tscables",
        determine_upgrade_option=True,
    )
    Seasons: int = Field(
        title="Seasons",
        description="Seasons",
    )
    Ratings: Any = Field(
        default=None,
        title="Ratings",
        description="Ratings",
    )
    LineType: str = Field(
        title="LineType",
        description="LineType",
        determine_upgrade_option=True,
    )
    like: Any = Field(
        default=None,
        title="like",
        description="like",
    )
    LineType: str = Field(
        title="LineType",
        description="LineType",
        determine_upgrade_option=True,
    )


class OpenDSSTransformerModel(CommonTransformerParameters):
    bus: str = Field(
        title="bus",
        description="bus",
    )
    buses: Any = Field(
        default=None,
        title="buses",
        description="buses",
    )
    enabled: Any = Field(
        default=None,
        title="enabled",
        description="enabled",
    )


class TransformerModel(OpenDSSTransformerModel, ExtraTransformerParams):
    name: str = Field(
        title="name",
        description="name. This is not a direct OpenDSS object property.",
    )


class TransformerCatalogModel(CommonTransformerParameters, ExtraTransformerParams):
    """Contains Transformer information needed for thermal upgrade analysis. Most fields can be directly obtained from the opendss models"""
    name: str = Field(
        title="name",
        description="name",
    )


class UpgradeTechnicalCatalogModel(UpgradeParamsBaseModel):
    """Contains Upgrades Technical Catalog needed for thermal upgrade analysis"""
    line: Optional[List[LineCatalogModel]] = Field(
        title="line",
        description="line catalog",
        default=[]
    )
    transformer: Optional[List[TransformerCatalogModel]] = Field(
        title="transformer",
        description="transformer catalog",
        default=[]
    )
    linecode: Optional[List[LineCodeCatalogModel]] = Field(
        title="linecode",
        description="linecode catalog",
        default=[]
    )
    geometry: Optional[List[LineGeometryCatalogModel]] = Field(
        title="linegeometry",
        description="linegeometry catalog",
        default=[]
    )


class ThermalUpgradeParamsModel(UpgradeParamsBaseModel):
    """Thermal Upgrade Parameters for all jobs in a simulation"""

    # Required fields
    transformer_upper_limit: float = Field(
        title="transformer_upper_limit",
        description="Transformer upper limit in per unit (example: 1.25)",
    )
    line_upper_limit: float = Field(
        title="line_upper_limit",
        description="Line upper limit in per unit (example: 1.25)",
    )
    line_design_pu: float = Field(
        title="line_design_pu",
        description="Line design in per unit (example: 0.75)",
    )
    transformer_design_pu: float = Field(
        title="transformer_design_pu",
        description="Transformer design in per unit (example: 0.75)",
    )
    voltage_upper_limit: float = Field(
        title="voltage_upper_limit",
        description="Voltage upper limit in per unit (example: 1.05)",
    )
    voltage_lower_limit: float = Field(
        title="voltage_lower_limit",
        description="Voltage lower limit in per unit (example: 0.95)",
    )
    read_external_catalog: bool = Field(
        title="read_external_catalog",
        description="Flag to determine whether external catalog is to be used (example: False)",
    )
    external_catalog: str = Field(
        title="external_catalog",
        description="Location to external upgrades technical catalog json file",
    )

    # Optional fields
    create_plots: Optional[bool] = Field(
        title="create_plots", description="Flag to enable or disable figure creation", default=True
    )
    parallel_transformers_limit: Optional[int] = Field(
        title="parallel_transformers_limit", description="Parallel transformer limit", default=4
    )
    parallel_lines_limit: Optional[int] = Field(
        title="parallel_lines_limit", description="Parallel lines limit", default=4
    )
    upgrade_iteration_threshold: Optional[int] = Field(
        title="upgrade_iteration_threshold", description="Upgrade iteration threshold", default=5
    )
    timepoint_multipliers: Optional[Dict] = Field(
        default=None,
        title="timepoint_multipliers",
        description='Dictionary to provide timepoint multipliers. example: timepoint_multipliers={"load_multipliers": {"with_pv": [1.2], "without_pv": [0.6]}}',
    )

    @field_validator("voltage_lower_limit")
    @classmethod
    def check_voltage_lower_limits(cls, voltage_lower_limit, info):
        # Skip the cross-check if the dependency failed its own validation; pydantic
        # already reports that error and info.data would otherwise raise KeyError.
        if "voltage_upper_limit" not in info.data:
            return voltage_lower_limit
        upper = info.data["voltage_upper_limit"]
        if upper <= voltage_lower_limit:
            raise ValueError(
                f"voltage_upper_limit={upper} must be greater than voltage_lower_limit={voltage_lower_limit}"
            )
        return voltage_lower_limit

    @field_validator("line_design_pu")
    @classmethod
    def check_line_design_pu(cls, line_design_pu, info):
        if "line_upper_limit" not in info.data:
            return line_design_pu
        upper = info.data["line_upper_limit"]
        if line_design_pu >= upper:
            raise ValueError(
                f"line_design_pu={line_design_pu} must be lesser than line_upper_limit={upper}"
            )
        return line_design_pu

    @field_validator("transformer_design_pu")
    @classmethod
    def check_transformer_design_pu(cls, transformer_design_pu, info):
        if "transformer_upper_limit" not in info.data:
            return transformer_design_pu
        upper = info.data["transformer_upper_limit"]
        if transformer_design_pu >= upper:
            raise ValueError(
                f"transformer_design_pu={transformer_design_pu} must be lesser than transformer_upper_limit={upper}"
            )
        return transformer_design_pu

    @field_validator("external_catalog")
    @classmethod
    def check_catalog(cls, external_catalog, info):
        if info.data.get("read_external_catalog"):
            if not Path(external_catalog).exists():
                raise ValueError(f"{external_catalog} does not exist")
            # Just verify that it constructs the model.
            UpgradeTechnicalCatalogModel(**load_data(external_catalog))
        return external_catalog

    @field_validator("timepoint_multipliers")
    @classmethod
    def check_timepoint_multipliers(cls, timepoint_multipliers):
        if timepoint_multipliers is None:
            return timepoint_multipliers
        if "load_multipliers" not in timepoint_multipliers:
            raise ValueError("load_multipliers must be defined in timepoint_multipliers")
        if ("with_pv" not in timepoint_multipliers["load_multipliers"]) and ("without_pv" not in timepoint_multipliers["load_multipliers"]):
            raise ValueError(
                'Either "with_pv" or "without_pv" must be defined in timepoint_multipliers["load_multipliers"]'
            )
        return timepoint_multipliers


class VoltageUpgradeParamsModel(UpgradeParamsBaseModel):
    """Voltage Upgrade Parameters for all jobs in a simulation"""

    # Required fields
    initial_upper_limit: float = Field(
        title="initial_upper_limit",
        description="Initial upper limit in per unit (example: 1.05)",
    )
    initial_lower_limit: float = Field(
        title="initial_lower_limit",
        description="Initial lower limit in per unit (example: 0.95)",
    )
    final_upper_limit: float = Field(
        title="final_upper_limit",
        description="Final upper limit in per unit (example: 1.05)",
    )
    final_lower_limit: float = Field(
        title="final_lower_limit",
        description="Final lower limit in per unit (example: 0.95)",
    )
    nominal_voltage: float = Field(
        title="nominal_voltage",
        description="Nominal voltage (volts) (example: 120)",
    )

    # Optional fields
    create_plots: Optional[bool] = Field(
        title="create_plots", 
        description="Flag to enable or disable figure creation", 
        default=True
    )
    capacitor_sweep_voltage_gap: float = Field(
        title="capacitor_sweep_voltage_gap",
        description="Capacitor sweep voltage gap (example: 1)",
        default=1.0,
    )
    reg_control_bands: List[int] = Field(
        title="reg_control_bands",
        description="Regulator control bands (example: [1, 2])",
        default=[1, 2],
    )
    reg_v_delta: float = Field(
        title="reg_v_delta",
        description="Regulator voltage delta (example: 0.5)",
        default=0.5,
    )
    max_regulators: int = Field(
        title="max_regulators",
        description="Maximum number of regulators",
        default=4,
    )
    place_new_regulators: bool = Field(
        title="place_new_regulators",
        description="Flag to enable or disable new regulator placement",
        default=True,
    )
    use_ltc_placement: bool = Field(
        title="use_ltc_placement",
        description="Flag to enable or disable substation LTC upgrades module",
        default=True,
    )
    timepoint_multipliers: dict = Field(
        title="timepoint_multipliers",
        description='Dictionary to provide timepoint multipliers. example: timepoint_multipliers={"load_multipliers": {"with_pv": [1.2], "without_pv": [0.6]}}',
        default=None,
    )
    capacitor_action_flag: bool = Field(
        title="capacitor_action_flag",
        description="Flag to enable or disable capacitor controls settings sweep module",
        default=True,
    )
    existing_regulator_sweep_action: bool = Field(
        title="existing_regulator_sweep_action",
        description="Flag to enable or disable existing regulator controls settings sweep module",
        default=True,
    )
    max_control_iterations: int = Field(
        title="max_control_iterations",
        description="Max control iterations to be set for OpenDSS",
        default=50,
    )

    @field_validator("initial_lower_limit")
    @classmethod
    def check_initial_voltage_lower_limits(cls, initial_lower_limit, info):
        if "initial_upper_limit" not in info.data:
            return initial_lower_limit
        upper = info.data["initial_upper_limit"]
        if upper <= initial_lower_limit:
            raise ValueError(
                f"initial_upper_limit={upper} must be greater than initial_lower_limit={initial_lower_limit}"
            )
        return initial_lower_limit

    @field_validator("final_lower_limit")
    @classmethod
    def check_final_voltage_lower_limits(cls, final_lower_limit, info):
        if "final_upper_limit" not in info.data:
            return final_lower_limit
        upper = info.data["final_upper_limit"]
        if upper <= final_lower_limit:
            raise ValueError(
                f"final_upper_limit={upper} must be greater than final_lower_limit={final_lower_limit}"
            )
        return final_lower_limit

    @field_validator("timepoint_multipliers")
    @classmethod
    def check_timepoint_multipliers(cls, timepoint_multipliers):
        if timepoint_multipliers is None:
            return timepoint_multipliers
        if "load_multipliers" not in timepoint_multipliers:
            raise ValueError("load_multipliers must be defined in timepoint_multipliers")
        if ("with_pv" not in timepoint_multipliers["load_multipliers"]) and ("without_pv" not in timepoint_multipliers["load_multipliers"]):
            raise ValueError(
                'Either "with_pv" or "without_pv" must be defined in timepoint_multipliers["load_multipliers"]'
            )
        return timepoint_multipliers


class UpgradeCostAnalysisGenericModel(BaseAnalysisModel):
    """Parameters for each job in a simulation"""

    name: str = Field(
        title="name",
        description="Unique name identifying the job",
    )
    opendss_model_file: str = Field(
        title="opendss_model_file",
        description="Path to file used load the simulation model files",
    )
    model_type: str = Field(
        title="model_type",
        description="Model type",
        default="UpgradeCostAnalysisGenericModel",
    )
    blocked_by: Set[str] = Field(
        title="blocked_by",
        description="Names of jobs that must finish before this job starts",
        default=set(),
    )
    estimated_run_minutes: Optional[int] = Field(
        default=None,
        title="estimated_run_minutes",
        description="Optionally advises the job execution manager on how long the job will run",
    )

    @field_validator("opendss_model_file")
    @classmethod
    def check_model_file(cls, opendss_model_file):
        if not Path(opendss_model_file).exists():
            raise ValueError(f"{opendss_model_file} does not exist")
        return opendss_model_file


class PyDssControllerModels(UpgradeParamsBaseModel):
    """Defines the settings for PyDSS controllers"""

    pv_controller: Optional[PvControllerModel] = Field(
        default=None,
        title="pv_controller", description="Settings for a PV controller"
    )


class UpgradeCostAnalysisSimulationModel(UpgradeParamsBaseModel):
    """Defines the jobs in an upgrade cost analysis simulation."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        use_enum_values=False,
    )

    thermal_upgrade_params: ThermalUpgradeParamsModel = Field(
        default=ThermalUpgradeParamsModel(**get_default_thermal_upgrade_params())
    )
    voltage_upgrade_params: VoltageUpgradeParamsModel = Field(
        default=VoltageUpgradeParamsModel(**get_default_voltage_upgrade_params())
    )
    upgrade_cost_database: str = Field(
        title="upgrade_cost_database",
        description="Database containing costs for each equipment type",
    )
    calculate_costs: bool = Field(
        title="calculate_costs",
        description="If True, calculate upgrade costs from database.",
        default=True,
    )
    upgrade_order: List[str] = Field(
        description="Order of upgrade algorithm. 'thermal' or 'voltage' can be removed from the "
        "simulation by excluding them from this parameter.",
        default=_SUPPORTED_UPGRADE_TYPES,
    )
    pydss_controllers: PyDssControllerModels = Field(
        title="pydss_controllers",
        description="If enable_pydss_controllers is True, these PyDSS controllers are applied to each corresponding element type.",
        default=PyDssControllerModels(),
    )
    plot_violations: bool = Field(
        title="plot_violations",
        description="If True, create plots of violations before and after simulation.",
        default=True,
    )
    enable_pydss_controllers: bool = Field(
        title="enable_pydss_controllers",
        description="Flag to enable/disable use of PyDSS controllers",
        default=False,
    )
    include_pf1: bool = Field(
        title="include_pf1",
        description="Include PF1 scenario (no controls) if pydss_controllers are defined.",
        default=True,
    )
    dc_ac_ratio: Optional[float] = Field(
        title="dc_ac_ratio", description="Apply DC-AC ratio for PV Systems", default=None
    )
    jobs: List[UpgradeCostAnalysisGenericModel]

    @field_validator("pydss_controllers", mode="before")
    @classmethod
    def handle_empty_pydss_controllers(cls, val):
        # Input configs may set this to an empty string or None to mean "no controllers".
        if not val:
            return {}
        return val

    @model_validator(mode="before")
    @classmethod
    def check_job_names(cls, values):
        # Runs before field validation; let normal validation report a missing/invalid
        # "jobs" with a clean error rather than raising a raw KeyError/TypeError here.
        if not isinstance(values, dict) or "jobs" not in values:
            return values
        names = set()
        for job in values["jobs"]:
            if job["name"] in names:
                raise ValueError(f"{job['name']} is duplicated")
            names.add(job["name"])
        return values

    @field_validator("calculate_costs")
    @classmethod
    def check_database(cls, calculate_costs, info):
        if calculate_costs:
            if "upgrade_cost_database" not in info.data:
                return calculate_costs
            if not Path(info.data["upgrade_cost_database"]).exists():
                raise ValueError(f"{info.data['upgrade_cost_database']} does not exist")
            # Just verify that it constructs the model.
            load_cost_database(info.data["upgrade_cost_database"])
        return calculate_costs

    @field_validator("upgrade_order")
    @classmethod
    def check_upgrade_order(cls, upgrade_order):
        diff = set(upgrade_order).difference(_SUPPORTED_UPGRADE_TYPES)
        if diff:
            raise ValueError(f"Unsupported values in upgrade_order: {diff}")
        return upgrade_order

    def has_pydss_controllers(self):
        """Return True if a PyDSS controller is defined.

        Returns
        -------
        bool

        """
        return self.pydss_controllers.pv_controller is not None
 
    
class TransformerUnitCostModel(UpgradeParamsBaseModel):
    """Contains Transformer Unit Cost Database Model"""
    
    phases: int = Field(
        title="phases",
        description="Number of phases",
    )
    primary_kV: float = Field(
        title="primary_kV",
        description="Transformer primary winding voltage, in kV",
    )
    secondary_kV: float = Field(
        title="secondary_kV",
        description="Transformer secondary winding voltage, in kV",
    )    
    num_windings: int = Field(
        title="num_windings",
        description="Number of windings",
    )
    primary_connection_type: str = Field(
        title="primary_connection_type",
        description="Transformer primary winding connection type. Should be wye or delta",
    )
    secondary_connection_type: str = Field(
        title="secondary_connection_type",
        description="Transformer secondary winding connection type. Should be wye or delta",
    )
    rated_kVA: float = Field(
        title="rated_kVA",
        description="Transformer Rated kVA",
    )
    cost: float = Field(
        title="cost",
        description="Transformer unit cost",
    )
    cost_units: str = Field(
        title="cost_units",
        description="Unit for cost. This should be in USD/unit",
    )
    
    @field_validator("cost_units")
    @classmethod
    def check_transformer_cost_units(cls, cost_units):
        if cost_units not in ("USD/unit"):
            raise ValueError("Incorrect cost units")
        return cost_units
    
    @field_validator("primary_connection_type")
    @classmethod
    def check_primary_connection(cls, primary_connection_type):
        if primary_connection_type not in ("wye", "delta"):
            raise ValueError("Incorrect transformer primary connection type")
        return primary_connection_type
    
    @field_validator("secondary_connection_type")
    @classmethod
    def check_secondary_connection(cls, secondary_connection_type):
        if secondary_connection_type not in ("wye", "delta"):
            raise ValueError("Incorrect transformer secondary connection type")
        return secondary_connection_type
        

class LineUnitCostModel(UpgradeParamsBaseModel):
    """Contains Line Unit Cost Database Model"""
    
    upgrade_type: str = Field(
        title="upgrade_type",
        description="Description of whether this is a new_line or reconductored_line",
    )
    phases: int = Field(
        title="phases",
        description="Number of phases",
    )
    voltage_kV: float = Field(
        title="voltage_kV",
        description="Voltage level in kV",
    )    
    ampere_rating: float = Field(
        title="ampere_rating",
        description="Line rating in amperes",
    )
    line_placement: str = Field(
        title="line_placement",
        description="Placement of line: overhead or underground",
    )
    cost_per_m: float = Field(
        title="cost_per_m",
        description="Cost per meter",
    )
    cost_units: str = Field(
        title="cost_units",
        description="Unit for cost. This should be in USD",
    )
    name: Optional[str] = Field(
        default=None,
        title="name",
        description="Line name. This is an optional parameter, and is not used.",
    )
    
    @field_validator("line_placement")
    @classmethod
    def check_line_placement(cls, line_placement):
        if line_placement not in ("underground", "overhead"):
            raise ValueError("Incorrect Line placement type. Acceptable values: overhead, underground.")
        return line_placement
    
    @field_validator("cost_units")
    @classmethod
    def check_line_cost_units(cls, cost_units):
        if cost_units not in ("USD"):
            raise ValueError("Incorrect cost units")
        return cost_units
    
    @field_validator("upgrade_type")
    @classmethod
    def check_line_upgrade_type(cls, upgrade_type):
        if upgrade_type not in ("new_line", "reconductored_line"):
            raise ValueError("Incorrect line upgrade_type")
        return upgrade_type
    
        
class ControlUnitCostModel(UpgradeParamsBaseModel):
    """Contains Control Changes Cost Database Model"""
    
    type: str = Field(
        title="type",
        description="Type of control setting",
    )
    cost: float = Field(
        title="cost",
        description="Control changes unit cost",
    )
    cost_units: str = Field(
        title="cost_units",
        description="Unit for cost. This should be in USD/unit",
    )
    
    @field_validator("cost_units")
    @classmethod
    def check_control_cost_units(cls, cost_units):
        if cost_units not in ("USD/unit"):
            raise ValueError("Incorrect cost units")
        return cost_units
    
    
class VRegUnitCostModel(TransformerUnitCostModel):
    """Contains Voltage Regulator Cost Database Model"""
    
    type: str = Field(
        title="type",
        description="This should be 'Add new voltage regulator transformer'.",
    )
    

class MiscUnitCostModel(UpgradeParamsBaseModel):
    """Contains Miscellaneous Cost Database Model"""
    
    description: str = Field(
        title="description",
        description="Description of whether this is a fixed cost to add or replace transformer. "
        "These are optional, and will be used if provided.",
    )
    total_cost: float = Field(
        title="total_cost",
        description="total_cost",
    )
    cost_units: str = Field(
        title="cost_units",
        description="Unit for cost. This should be in USD/unit",
    )
    
    @field_validator("cost_units")
    @classmethod
    def check_misc_cost_units(cls, cost_units):
        if cost_units not in ("USD/unit"):
            raise ValueError("Incorrect cost units")
        return cost_units
    
    @field_validator("description")
    @classmethod
    def check_misc_description(cls, description):
        if description not in ("Replace transformer (fixed cost)", "Add new transformer (fixed cost)"):
            raise ValueError("Incorrect Miscellaneous Description")
        return description
    

class UpgradeCostDatabaseModel(UpgradeParamsBaseModel):
    """Contains Upgrades Unit Cost Database needed for cost analysis"""
    
    transformers: List[TransformerUnitCostModel] = Field(
        title="transformers",
        description="This consists of all transformer unit costs",
        default=[]
    )
    lines: List[LineUnitCostModel] = Field(
        title="lines",
        description="This consists of all line unit costs",
        default=[]
    )
    control_changes: List[ControlUnitCostModel] = Field(
        title="control_changes",
        description="This consists of all control changes unit costs",
        default=[]
    )
    voltage_regulators: List[VRegUnitCostModel] = Field(
        title="voltage_regulators",
        description="This consists of all voltage regulator unit costs",
        default=[]
    )
    misc: List[MiscUnitCostModel] = Field(
        title="misc",
        description="This consists of all miscellaneous unit costs",
        default=[]
    )


def load_cost_database(filepath):
    xfmr_cost_database = pd.read_excel(filepath, "transformers")
    line_cost_database = pd.read_excel(filepath, "lines")
    controls_cost_database = pd.read_excel(filepath, "control_changes")
    voltage_regulators_cost_database = pd.read_excel(filepath, "voltage_regulators")
    misc_database = pd.read_excel(filepath, "misc")

    transformers = xfmr_cost_database.to_dict(orient="records")
    lines = line_cost_database.to_dict(orient="records")
    control_changes = controls_cost_database.to_dict(orient="records")
    voltage_regulators = voltage_regulators_cost_database.to_dict(orient="records")
    misc = misc_database.to_dict(orient="records")

    # perform validation of input cost database using pydantic models
    # Check the first row of each type to ensure that the columns are correct.
    # If they aren't, pydantic will print errors for each row.
    for name, rows, cls in (
        ("transformers", transformers, TransformerUnitCostModel),
        ("lines", lines, LineUnitCostModel),
        ("control_changes", control_changes, ControlUnitCostModel),
        ("voltage_regulators", voltage_regulators, VRegUnitCostModel),
        ("misc", misc, MiscUnitCostModel),
    ):
        if rows:
            try:
                cls(**rows[0])
            except ValidationError:
                logger.error("Failed to validate cost database file=%s sheet=%s", filepath, name)
                raise

    UpgradeCostDatabaseModel(
        transformers=transformers,
        lines=lines,
        control_changes=control_changes,
        voltage_regulators=voltage_regulators,
        misc=misc,
    )
    return (
        xfmr_cost_database,
        line_cost_database,
        controls_cost_database,
        voltage_regulators_cost_database,
        misc_database,
    )
