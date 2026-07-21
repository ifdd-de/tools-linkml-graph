from pathlib import Path

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_graph_explorer.viz_config import load_viz_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def schema_path() -> Path:
    return PROJECT_ROOT / "schema" / "grid_assets.yaml"


@pytest.fixture(scope="session")
def data_path() -> Path:
    return PROJECT_ROOT / "data" / "circuit_sunville.yaml"


@pytest.fixture(scope="session")
def viz_config_path() -> Path:
    return PROJECT_ROOT / "config" / "viz.yaml"


@pytest.fixture(scope="session")
def schema_view(schema_path) -> SchemaView:
    return SchemaView(str(schema_path))


@pytest.fixture(scope="session")
def viz_config(viz_config_path, schema_view):
    return load_viz_config(viz_config_path, schema_view)


@pytest.fixture(scope="session")
def root_object(data_path) -> dict:
    return yaml.safe_load(data_path.read_text(encoding="utf-8"))
