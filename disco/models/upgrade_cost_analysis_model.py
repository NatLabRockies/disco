from typing import Optional

from pydantic import Field, ConfigDict

from disco.models.base import (
    BaseAnalysisModel,
    DiscoBaseModel,
    OpenDssDeploymentModel,
    SimulationModel
)


class ParameterOverridesModel(DiscoBaseModel):
    # TODO: Add upgrade parameters
    model_config = ConfigDict(validate_assignment=True)


class UpgradeCostAnalysisModel(BaseAnalysisModel):
    deployment: OpenDssDeploymentModel = Field(
        title="deployment",
        description="PV deployment on feeder",
        default=None,
    )
    simulation: SimulationModel = Field(
        title="simulation",
        description="Simulation parameters with PV deployment",
        default=None,
    )
    parameter_overrides: Optional[ParameterOverridesModel] = Field(
        title="parameter_overrides",
        default={},
        description="Override default upgrade parameters on job level",
    )
    
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
