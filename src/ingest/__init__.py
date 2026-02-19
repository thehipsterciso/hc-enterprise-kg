"""Data ingestion for the knowledge graph."""

from ingest.base import AbstractIngestor, IngestResult
from ingest.csv_ingestor import CSVIngestor
from ingest.json_ingestor import JSONIngestor

__all__ = ["AbstractIngestor", "CSVIngestor", "IngestResult", "JSONIngestor"]
