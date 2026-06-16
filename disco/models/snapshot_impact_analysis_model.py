"""Defines snapshot impact analysis data model"""

from typing import Optional

from pydantic import Field, ConfigDict

from .base import ImpactAnalysisBaseModel


class SnapshotImpactAnalysisModel(ImpactAnalysisBaseModel):
    """Data model for snapshot impact analysis"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    include_voltage_deviation: Optional[bool] = Field(
        title="include_voltage_deviation",
        default=False,
        description="Whether include voltage deviation or not",
    )
