"""Assembly of the standalone exploration HTML."""

from __future__ import annotations

import json
from html import escape
from importlib import resources
from pathlib import Path

import yaml
from linkml_runtime import SchemaView

from .graph import build_elements
from .i18n import resolve_language, translator
from .viz_config import VizConfig, load_viz_config

BASE_NODE_STYLE = {
    "label": "data(label)",
    "text-valign": "center",
    "text-wrap": "wrap",
    "text-max-width": 100,
    "width": 120,
    "height": 46,
    "border-width": 1,
    "border-color": "#6b7280",
    "font-size": 11,
}

BASE_EDGE_STYLE = {
    "label": "data(label)",
    "font-size": 9,
    "curve-style": "bezier",
    "target-arrow-shape": "triangle",
    "text-rotation": "autorotate",
    "width": 1.5,
    "text-background-color": "#ffffff",
    "text-background-opacity": 0.8,
}


def build_stylesheet(
    config: VizConfig,
    node_classes: list[str],
    edge_labels: list[str],
) -> list[dict]:
    stylesheet = [
        {"selector": "node", "style": BASE_NODE_STYLE},
        {"selector": "edge", "style": BASE_EDGE_STYLE},
    ]
    for class_name in node_classes:
        style = config.node_style(class_name)
        stylesheet.append({
            "selector": f'node[type = "{class_name}"]',
            "style": {"background-color": style.color, "shape": style.shape},
        })
    for edge_label in edge_labels:
        style = config.edge_style(edge_label)
        stylesheet.append({
            "selector": f'edge[label = "{edge_label}"]',
            "style": {
                "line-color": style.color,
                "target-arrow-color": style.color,
                "line-style": style.line_style,
            },
        })
    stylesheet += [
        {"selector": ".highlighted",
         "style": {"border-width": 3, "border-color": "#f59e0b"}},
        {"selector": ".hidden", "style": {"display": "none"}},
    ]
    return stylesheet


def render_explorer_html(
    schema_path: Path,
    data_path: Path,
    viz_config_path: Path,
    out_dir: Path,
    root_class: str,
    positions_path: Path | None = None,
    language: str | None = None,
) -> Path:
    schema_view = SchemaView(str(schema_path))
    config = load_viz_config(viz_config_path, schema_view)
    root_object = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    _ = translator(language)

    elements = build_elements(schema_view, root_object, root_class, config)
    node_classes = sorted({node["data"]["type"] for node in elements["nodes"]})
    edge_labels = sorted({edge["data"]["label"] for edge in elements["edges"]})

    html = _read_packaged("template.html")
    replacements = {
        "__LANG__": resolve_language(language),
        "__TITLE__": escape(_("Graph exploration")),
        "__L_RESET__": escape(_("Default view")),
        "__L_FIT__": escape(_("Fit")),
        "__L_SAVE__": escape(_("Save layout")),
        "__L_LOAD__": escape(_("Load layout")),
        "__L_LOAD_ERROR__": escape(_("Could not read layout file: ")),
        "__TOGGLES__": _toggle_markup(node_classes),
        "__GRAPH_DATA__": json.dumps(elements, ensure_ascii=False, indent=1),
        "__LAYOUT_DATA__": _layout_json(positions_path),
        "__LAYOUT_FILENAME__": f"{data_path.stem}_layout.json",
        "__STYLESHEET__": json.dumps(
            build_stylesheet(config, node_classes, edge_labels), indent=1
        ),
        "__CYTOSCAPE_BUNDLE__": _read_packaged("vendor/cytoscape.min.js"),
    }
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{data_path.stem}_explorer.html"
    target.write_text(html, encoding="utf-8")
    return target


def _toggle_markup(node_classes: list[str]) -> str:
    return "\n".join(
        f'<label><input type="checkbox" class="cls-toggle" '
        f'value="{escape(name)}" checked> {escape(name)}</label>'
        for name in node_classes
    )


def _layout_json(positions_path: Path | None) -> str:
    if positions_path is None:
        return "null"
    saved = json.loads(positions_path.read_text(encoding="utf-8"))
    if not isinstance(saved, dict) or "positions" not in saved:
        raise ValueError(
            f"{positions_path}: expected layout format "
            '{"positions": {...}, "zoom": ..., "pan": {...}}'
        )
    return json.dumps(saved, ensure_ascii=False)


def _read_packaged(name: str) -> str:
    return resources.files(__package__).joinpath(name).read_text(encoding="utf-8")
