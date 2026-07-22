import json
import re

import pytest

from linkml_graph_explorer.explorer import build_stylesheet, render_explorer_html


def embedded_json(html, element_id):
    match = re.search(
        rf'<script type="application/json" id="{element_id}">(.*?)</script>',
        html,
        re.S,
    )
    return json.loads(match.group(1))


def test_stylesheet_contains_class_and_edge_rules(viz_config):
    stylesheet = build_stylesheet(
        viz_config, ["Asset", "Location"], ["installed_at", "part_of_circuit"]
    )
    selectors = {rule["selector"] for rule in stylesheet}
    assert 'node[type = "Location"]' in selectors
    assert 'edge[label = "part_of_circuit"]' in selectors

    location_rule = next(
        rule for rule in stylesheet
        if rule["selector"] == 'node[type = "Location"]'
    )
    assert location_rule["style"]["background-color"] == "#bbf7d0"
    assert location_rule["style"]["shape"] == "hexagon"

    dashed_rule = next(
        rule for rule in stylesheet
        if rule["selector"] == 'edge[label = "part_of_circuit"]'
    )
    assert dashed_rule["style"]["line-style"] == "dashed"


def test_render_creates_selfcontained_html(
    schema_path, data_path, viz_config_path, tmp_path
):
    target = render_explorer_html(
        schema_path, data_path, viz_config_path, tmp_path, "GridModel"
    )
    html = target.read_text(encoding="utf-8")
    assert target.name == "circuit_sunville_explorer.html"
    assert "Cytoscape Consortium" in html
    assert embedded_json(html, "layout-data") is None

    graph_data = embedded_json(html, "graph-data")
    assert len(graph_data["nodes"]) == 10
    assert len(graph_data["edges"]) == 13
    assert html.count('class="cls-toggle"') == 3


def test_render_bakes_in_layout(
    schema_path, data_path, viz_config_path, tmp_path
):
    layout = {"zoom": 0.8, "pan": {"x": 10, "y": 20},
              "positions": {"SUB-SNV": {"x": 1, "y": 2}}}
    layout_file = tmp_path / "layout.json"
    layout_file.write_text(json.dumps(layout), encoding="utf-8")

    target = render_explorer_html(
        schema_path, data_path, viz_config_path, tmp_path, "GridModel",
        positions_path=layout_file,
    )
    baked = embedded_json(target.read_text(encoding="utf-8"), "layout-data")
    assert baked == layout


def test_render_rejects_malformed_layout(
    schema_path, data_path, viz_config_path, tmp_path
):
    layout_file = tmp_path / "layout.json"
    layout_file.write_text('{"zoom": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="expected layout format"):
        render_explorer_html(
            schema_path, data_path, viz_config_path, tmp_path, "GridModel",
            positions_path=layout_file,
        )


def test_every_toolbar_button_has_a_click_handler(
    schema_path, data_path, viz_config_path, tmp_path
):
    target = render_explorer_html(
        schema_path, data_path, viz_config_path, tmp_path, "GridModel"
    )
    html = target.read_text(encoding="utf-8")
    button_ids = re.findall(r'<button id="([^"]+)"', html)
    assert len(button_ids) == 7
    for button_id in button_ids:
        assert f'getElementById("{button_id}")' in html, (
            f"button {button_id!r} has no event handler"
        )


def test_render_translates_ui_strings(
    schema_path, data_path, viz_config_path, tmp_path
):
    target = render_explorer_html(
        schema_path, data_path, viz_config_path, tmp_path, "GridModel",
        language="de",
    )
    html = target.read_text(encoding="utf-8")
    assert "Layout speichern" in html
    assert "Standarddarstellung" in html
    assert '<html lang="de">' in html


def test_only_configured_engines_are_embedded(
    schema_path, data_path, tmp_path, schema_view
):
    fcose_only = tmp_path / "viz.yaml"
    fcose_only.write_text(
        "layout:\n  engines:\n    fcose: {}\n", encoding="utf-8"
    )
    target = render_explorer_html(
        schema_path, data_path, fcose_only, tmp_path, "GridModel"
    )
    html = target.read_text(encoding="utf-8")
    assert "cytoscapeFcose" in html
    assert "cytoscapeElk" not in html
    assert '<option value="fcose" selected>' in html
    assert 'id="compact-toggle"' not in html


def test_elk_engine_is_embedded_when_configured(
    schema_path, data_path, viz_config_path, tmp_path
):
    target = render_explorer_html(
        schema_path, data_path, viz_config_path, tmp_path, "GridModel"
    )
    html = target.read_text(encoding="utf-8")
    assert "cytoscapeElk" in html
    assert '<option value="elk">' in html
    assert 'id="compact-toggle"' in html
    assert 'id="btn-png"' in html


def test_stylesheet_hides_derived_edges_by_default(viz_config):
    stylesheet = build_stylesheet(viz_config, ["Circuit"], [])
    rules = {rule["selector"]: rule["style"] for rule in stylesheet}
    assert rules["edge.derived"]["display"] == "none"
    assert rules["edge.derived.compact"]["display"] == "element"
    assert rules['edge[relation = "Circuit"]']["line-color"] == "#fde68a"
