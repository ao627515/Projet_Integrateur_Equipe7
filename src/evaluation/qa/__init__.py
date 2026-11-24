"""Contrôle qualité déterministe et découpage stratifié groupé 70/30."""

from src.evaluation.qa.config import QAConfig
from src.evaluation.qa.pipeline import DatasetQAPipeline

__all__ = ["DatasetQAPipeline", "QAConfig"]
