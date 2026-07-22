"""Loading and schema validation of the visualization configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from linkml_runtime import SchemaView


KNOWN_ENGINES = ("fcose", "elk")
PARENT = "_parent_"


@dataclass(frozen=True)
class NodeStyle:
    color: str
    shape: str


@dataclass(frozen=True)
class EdgeStyle:
    color: str
    line_style: str


@dataclass(frozen=True)
class CollapseRule:
    source_slot: str
    target_slot: str


@dataclass(frozen=True)
class LayoutConfig:
    default: str
    engines: dict[str, dict]


@dataclass(frozen=True)
class VizConfig:
    label_slot: str
    detail_slot: str
    default_node: NodeStyle
    default_edge: EdgeStyle
    class_styles: dict[str, NodeStyle]
    edge_styles: dict[str, EdgeStyle]
    layout: LayoutConfig
    collapse: dict[str, CollapseRule]

    def node_style(self, class_name: str) -> NodeStyle:
        return self.class_styles.get(class_name, self.default_node)

    def edge_style(self, slot_name: str) -> EdgeStyle:
        return self.edge_styles.get(slot_name, self.default_edge)


_FALLBACK_NODE = NodeStyle(color="#e5e7eb", shape="round-rectangle")
_FALLBACK_EDGE = EdgeStyle(color="#9ca3af", line_style="solid")


def load_viz_config(path: Path, schema_view: SchemaView) -> VizConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    defaults = raw.get("defaults", {})
    default_node = _node_style(defaults.get("node", {}), _FALLBACK_NODE)
    default_edge = _edge_style(defaults.get("edge", {}), _FALLBACK_EDGE)

    config = VizConfig(
        label_slot=raw.get("label_slot", "name"),
        detail_slot=raw.get("detail_slot", "description"),
        default_node=default_node,
        default_edge=default_edge,
        class_styles={
            name: _node_style(style, default_node)
            for name, style in (raw.get("classes") or {}).items()
        },
        edge_styles={
            name: _edge_style(style, default_edge)
            for name, style in (raw.get("edges") or {}).items()
        },
        layout=_layout_config(raw.get("layout") or {}),
        collapse={
            name: CollapseRule(rule["source_slot"], rule["target_slot"])
            for name, rule in (raw.get("collapse") or {}).items()
        },
    )
    _validate_against_schema(config, schema_view, path)
    return config


def _layout_config(raw: dict) -> LayoutConfig:
    engines = raw.get("engines") or {"fcose": {}}
    return LayoutConfig(
        default=raw.get("default", next(iter(engines))),
        engines={name: options or {} for name, options in engines.items()},
    )


def _node_style(raw: dict, default: NodeStyle) -> NodeStyle:
    return NodeStyle(
        color=raw.get("color", default.color),
        shape=raw.get("shape", default.shape),
    )


def _edge_style(raw: dict, default: EdgeStyle) -> EdgeStyle:
    return EdgeStyle(
        color=raw.get("color", default.color),
        line_style=raw.get("line_style", default.line_style),
    )


def _validate_against_schema(
    config: VizConfig, schema_view: SchemaView, source: Path
) -> None:
    known_classes = set(schema_view.all_classes())
    known_slots = set(schema_view.all_slots())

    problems = []
    problems += [
        f"unknown class {name!r}"
        for name in config.class_styles
        if name not in known_classes
    ]
    problems += [
        f"unknown edge slot {name!r}"
        for name in config.edge_styles
        if name not in known_slots
    ]
    for role, slot in (("label_slot", config.label_slot),
                       ("detail_slot", config.detail_slot)):
        if slot not in known_slots:
            problems.append(f"{role} {slot!r} is not a slot of the schema")

    problems += [
        f"unknown layout engine {name!r} (known: {KNOWN_ENGINES})"
        for name in config.layout.engines
        if name not in KNOWN_ENGINES
    ]
    if config.layout.default not in config.layout.engines:
        problems.append(
            f"default engine {config.layout.default!r} is not in engines"
        )

    for class_name, rule in config.collapse.items():
        if class_name not in known_classes:
            problems.append(f"collapse: unknown class {class_name!r}")
            continue
        class_slots = {
            slot.name for slot in schema_view.class_induced_slots(class_name)
            if slot.range in known_classes
        }
        for role, slot in (("source", rule.source_slot),
                           ("target", rule.target_slot)):
            if role == "source" and slot == PARENT:
                continue
            if slot not in class_slots:
                problems.append(
                    f"collapse {class_name}: {slot!r} is not an "
                    f"object-valued slot of that class (or {PARENT!r})"
                )

    if problems:
        raise ValueError(f"{source}: " + "; ".join(problems))
