import tomllib
from pathlib import Path


def load_pyproject() -> dict:
    path = Path("pyproject.toml")
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return data


def get_version_from_toml() -> str:
    """Get version string from pyproject.toml"""
    data = load_pyproject()
    return data.get("project", {}).get("version")
