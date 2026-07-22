from pathlib import Path

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_graph_explorer.graph import build_elements
from linkml_graph_explorer.viz_config import load_viz_config

SCHEMA = """
id: https://example.org/inlined-test
name: inlined_test
prefixes: {linkml: https://w3id.org/linkml/}
default_range: string
imports: [linkml:types]
classes:
  Root:
    tree_root: true
    slots: [systems]
  System:
    slots: [id, name, outgoing_flows, peers]
  Flow:
    slots: [id, name, to_system]
slots:
  id: {identifier: true}
  name: {}
  systems: {range: System, multivalued: true, inlined: true, inlined_as_list: true}
  outgoing_flows: {range: Flow, multivalued: true, inlined: true, inlined_as_list: true}
  peers: {range: System, multivalued: true}
  to_system: {range: System}
"""

DATA = """
systems:
  - id: SYS-A
    name: System A
    peers: [SYS-B, SYS-C]
    outgoing_flows:
      - {id: FLOW-1, name: telemetry, to_system: SYS-B}
  - id: SYS-B
    name: System B
  - id: SYS-C
    name: System C
"""

VIZ = """
label_slot: name
detail_slot: name
collapse:
  Flow: {source_slot: _parent_, target_slot: to_system}
"""


@pytest.fixture(scope="module")
def inlined_schema_view(tmp_path_factory) -> SchemaView:
    path = tmp_path_factory.mktemp("inlined") / "schema.yaml"
    path.write_text(SCHEMA, encoding="utf-8")
    return SchemaView(str(path))


@pytest.fixture(scope="module")
def inlined_config(inlined_schema_view, tmp_path_factory):
    path = tmp_path_factory.mktemp("inlined") / "viz.yaml"
    path.write_text(VIZ, encoding="utf-8")
    return load_viz_config(path, inlined_schema_view)


@pytest.fixture(scope="module")
def elements(inlined_schema_view, inlined_config) -> dict:
    return build_elements(
        inlined_schema_view, yaml.safe_load(DATA), "Root", inlined_config
    )


def edge_triples(elements):
    return {
        (e["data"]["source"], e["data"]["label"], e["data"]["target"])
        for e in elements["edges"]
    }


def test_inlined_instances_become_nodes(elements):
    node_ids = {n["data"]["id"] for n in elements["nodes"]}
    assert node_ids == {"SYS-A", "SYS-B", "SYS-C", "FLOW-1"}


def test_containment_edge_links_parent_to_inlined_instance(elements):
    assert ("SYS-A", "outgoing_flows", "FLOW-1") in edge_triples(elements)


def test_multivalued_references_yield_one_edge_per_entry(elements):
    triples = edge_triples(elements)
    assert ("SYS-A", "peers", "SYS-B") in triples
    assert ("SYS-A", "peers", "SYS-C") in triples


def test_reference_slot_of_inlined_instance_becomes_edge(elements):
    assert ("FLOW-1", "to_system", "SYS-B") in edge_triples(elements)


def test_parent_collapse_contracts_flow_to_system_pair(elements):
    derived = [e for e in elements["edges"] if "relation" in e["data"]]
    assert len(derived) == 1
    data = derived[0]["data"]
    assert (data["source"], data["target"]) == ("SYS-A", "SYS-B")
    assert data["relation"] == "Flow"
    assert data["label"] == "telemetry"


def test_compact_dict_form_is_supported(inlined_schema_view, inlined_config):
    data = {"systems": {
        "SYS-X": {"name": "System X",
                  "outgoing_flows": [
                      {"id": "FLOW-9", "name": "sync", "to_system": "SYS-X"}]},
    }}
    elements = build_elements(inlined_schema_view, data, "Root", inlined_config)
    node_ids = {n["data"]["id"] for n in elements["nodes"]}
    assert node_ids == {"SYS-X", "FLOW-9"}
    assert ("SYS-X", "outgoing_flows", "FLOW-9") in edge_triples(elements)


def test_collapse_parent_marker_passes_validation(inlined_config):
    assert inlined_config.collapse["Flow"].source_slot == "_parent_"
