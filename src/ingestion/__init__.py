"""Pipeline d'ingestion et d'OCR local des PDF officiels du Code du travail 2026."""

from src.ingestion.config import ExtractionConfig
from src.ingestion.pipeline import IngestionPipeline

__all__ = ["ExtractionConfig", "IngestionPipeline"]
