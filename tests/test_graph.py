from linkml_graph_explorer.graph import build_elements


def edge_triples(elements):
    return {
        (edge["data"]["source"], edge["data"]["label"], edge["data"]["target"])
        for edge in elements["edges"]
    }


def node_by_id(elements, identifier):
    return next(
        node["data"] for node in elements["nodes"]
        if node["data"]["id"] == identifier
    )


def test_all_instances_become_nodes(schema_view, root_object, viz_config):
    elements = build_elements(schema_view, root_object, "GridModel", viz_config)
    assert len(elements["nodes"]) == 9


def test_object_valued_slots_become_edges(schema_view, root_object, viz_config):
    elements = build_elements(schema_view, root_object, "GridModel", viz_config)
    triples = edge_triples(elements)
    assert ("AST-T1", "installed_at", "SUB-SNV") in triples
    assert ("AST-L1", "part_of_circuit", "CIR-380-01") in triples
    assert ("CIR-380-01", "from_location", "SUB-SNV") in triples
    assert ("CIR-380-01", "to_location", "SUB-LST") in triples
    assert len(triples) == 9


def test_node_label_comes_from_label_slot(schema_view, root_object, viz_config):
    elements = build_elements(schema_view, root_object, "GridModel", viz_config)
    assert node_by_id(elements, "AST-T1")["label"] == "Transformer T1"


def test_detail_text_starts_with_description(schema_view, root_object, viz_config):
    elements = build_elements(schema_view, root_object, "GridModel", viz_config)
    detail = node_by_id(elements, "AST-T1")["detail"]
    assert detail.startswith("300 MVA power transformer")
    assert "voltage_kv: 380" in detail
    assert "commissioned_on: 1998-06-15" in detail


def test_detail_text_excludes_object_valued_slots(
    schema_view, root_object, viz_config
):
    detail = node_by_id(
        build_elements(schema_view, root_object, "GridModel", viz_config),
        "AST-T1",
    )["detail"]
    assert "installed_at" not in detail


def test_edges_to_missing_nodes_are_dropped(schema_view, viz_config):
    data = {
        "model_name": "dangling",
        "assets": [{
            "id": "AST-X",
            "name": "Orphan",
            "installed_at": "SUB-DOES-NOT-EXIST",
        }],
    }
    elements = build_elements(schema_view, data, "GridModel", viz_config)
    assert len(elements["nodes"]) == 1
    assert elements["edges"] == []


def test_node_without_optional_slots_gets_class_as_detail(
    schema_view, viz_config
):
    data = {"model_name": "minimal",
            "locations": [{"id": "L1", "name": "Bare location"}]}
    elements = build_elements(schema_view, data, "GridModel", viz_config)
    assert node_by_id(elements, "L1")["detail"] == "Location"
