import pytest

from linkml_graph_explorer.viz_config import load_viz_config


def test_configured_class_style_is_loaded(viz_config):
    assert viz_config.node_style("Location").color == "#bbf7d0"
    assert viz_config.node_style("Location").shape == "hexagon"


def test_unconfigured_class_falls_back_to_default(viz_config):
    assert viz_config.node_style("GridModel") == viz_config.default_node


def test_configured_edge_style_is_loaded(viz_config):
    assert viz_config.edge_style("part_of_circuit").line_style == "dashed"


def test_unconfigured_edge_falls_back_to_default(viz_config):
    assert viz_config.edge_style("installed_somewhere") == viz_config.default_edge


def test_label_and_detail_slots(viz_config):
    assert viz_config.label_slot == "name"
    assert viz_config.detail_slot == "description"


def test_empty_config_yields_fallback_defaults(tmp_path, schema_view):
    empty = tmp_path / "viz.yaml"
    empty.write_text("{}", encoding="utf-8")
    config = load_viz_config(empty, schema_view)
    assert config.default_node.shape == "round-rectangle"
    assert config.class_styles == {}


def test_unknown_class_is_rejected(tmp_path, schema_view):
    bad = tmp_path / "viz.yaml"
    bad.write_text("classes:\n  NoSuchClass: {color: '#fff'}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="NoSuchClass"):
        load_viz_config(bad, schema_view)


def test_unknown_edge_slot_is_rejected(tmp_path, schema_view):
    bad = tmp_path / "viz.yaml"
    bad.write_text("edges:\n  no_such_slot: {color: '#fff'}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no_such_slot"):
        load_viz_config(bad, schema_view)


def test_unknown_label_slot_is_rejected(tmp_path, schema_view):
    bad = tmp_path / "viz.yaml"
    bad.write_text("label_slot: no_such_slot\n", encoding="utf-8")
    with pytest.raises(ValueError, match="label_slot"):
        load_viz_config(bad, schema_view)


def test_layout_section_is_parsed(viz_config):
    assert viz_config.layout.default == "fcose"
    assert set(viz_config.layout.engines) == {"fcose", "elk"}
    assert viz_config.layout.engines["elk"]["elk"]["algorithm"] == "layered"


def test_missing_layout_section_defaults_to_fcose(tmp_path, schema_view):
    minimal = tmp_path / "viz.yaml"
    minimal.write_text("{}", encoding="utf-8")
    config = load_viz_config(minimal, schema_view)
    assert config.layout.default == "fcose"
    assert config.layout.engines == {"fcose": {}}
    assert config.collapse == {}


def test_unknown_engine_is_rejected(tmp_path, schema_view):
    bad = tmp_path / "viz.yaml"
    bad.write_text("layout:\n  engines:\n    dagre: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="dagre"):
        load_viz_config(bad, schema_view)


def test_default_engine_must_be_configured(tmp_path, schema_view):
    bad = tmp_path / "viz.yaml"
    bad.write_text(
        "layout:\n  default: elk\n  engines:\n    fcose: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="default engine"):
        load_viz_config(bad, schema_view)


def test_collapse_is_parsed(viz_config):
    rule = viz_config.collapse["Circuit"]
    assert (rule.source_slot, rule.target_slot) == \
        ("from_location", "to_location")


def test_collapse_unknown_class_is_rejected(tmp_path, schema_view):
    bad = tmp_path / "viz.yaml"
    bad.write_text(
        "collapse:\n  NoSuchClass:\n    source_slot: from_location\n"
        "    target_slot: to_location\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="NoSuchClass"):
        load_viz_config(bad, schema_view)


def test_collapse_slot_must_be_object_valued(tmp_path, schema_view):
    bad = tmp_path / "viz.yaml"
    bad.write_text(
        "collapse:\n  Circuit:\n    source_slot: voltage_kv\n"
        "    target_slot: to_location\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="voltage_kv"):
        load_viz_config(bad, schema_view)
