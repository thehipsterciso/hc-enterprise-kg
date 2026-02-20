"""Enterprise Knowledge Graph for cybersecurity, data, and AI research."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("hc-enterprise-kg")
except PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for editable installs without metadata
