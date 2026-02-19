"""Automatic knowledge graph construction pipeline."""

from auto.base import ExtractionResult, LinkingResult, PipelineResult, ResolutionResult
from auto.pipeline import AutoKGPipeline

__all__ = [
    "AutoKGPipeline",
    "ExtractionResult",
    "LinkingResult",
    "PipelineResult",
    "ResolutionResult",
]
