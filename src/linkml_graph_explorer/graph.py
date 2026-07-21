"""Schema-driven derivation of graph elements from LinkML instance data.

Object-valued slots (range = class with an identifier) become directed
edges labeled with the slot name; literal-valued slots feed the node
detail text shown on mouse-over.
"""

from __future__ import annotations

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SlotDefinition

from .viz_config import VizConfig


def build_elements(
    schema_view: SchemaView,
    root_object: dict,
    root_class: str,
    config: VizConfig,
) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []

    for member_class, instance in _instances(schema_view, root_object, root_class):
        nodes.append(_node_for(schema_view, member_class, instance, config))
        edges.extend(_edges_for(schema_view, member_class, instance))

    return {"nodes": nodes, "edges": _drop_dangling(edges, nodes)}


def _instances(schema_view: SchemaView, root_object: dict, root_class: str):
    for slot in schema_view.class_induced_slots(root_class):
        member_class = _range_class(schema_view, slot)
        if member_class is None or not slot.multivalued:
            continue
        if schema_view.get_identifier_slot(member_class) is None:
            continue
        for instance in root_object.get(slot.name) or []:
            yield member_class, instance


def _node_for(
    schema_view: SchemaView, member_class: str, instance: dict, config: VizConfig
) -> dict:
    identifier = _identifier_of(schema_view, member_class, instance)
    return {"data": {
        "id": identifier,
        "label": instance.get(config.label_slot, identifier),
        "type": member_class,
        "detail": _detail_text(schema_view, member_class, instance, config),
    }}


def _edges_for(schema_view: SchemaView, member_class: str, instance: dict):
    source = _identifier_of(schema_view, member_class, instance)
    for slot in schema_view.class_induced_slots(member_class):
        target = instance.get(slot.name)
        if target is None or _range_class(schema_view, slot) is None:
            continue
        yield {"data": {
            "id": f"{source}--{slot.name}--{target}",
            "source": source,
            "target": str(target),
            "label": slot.name,
            "detail": (slot.description or slot.name).strip(),
        }}


def _detail_text(
    schema_view: SchemaView, member_class: str, instance: dict, config: VizConfig
) -> str:
    identifier_slot = schema_view.get_identifier_slot(member_class).name
    skipped = {identifier_slot, config.label_slot, config.detail_slot}

    lines = []
    primary = instance.get(config.detail_slot)
    if primary:
        lines.append(str(primary).strip())

    for slot in schema_view.class_induced_slots(member_class):
        value = instance.get(slot.name)
        if value in (None, "", []):
            continue
        if slot.name in skipped or _range_class(schema_view, slot) is not None:
            continue
        lines.append(f"{slot.name}: {value}")

    return "\n".join(lines) or member_class


def _identifier_of(schema_view: SchemaView, member_class: str, instance: dict) -> str:
    return str(instance[schema_view.get_identifier_slot(member_class).name])


def _range_class(schema_view: SchemaView, slot: SlotDefinition) -> str | None:
    if slot.range and slot.range in schema_view.all_classes():
        return slot.range
    return None


def _drop_dangling(edges: list[dict], nodes: list[dict]) -> list[dict]:
    node_ids = {node["data"]["id"] for node in nodes}
    return [
        edge for edge in edges
        if edge["data"]["source"] in node_ids and edge["data"]["target"] in node_ids
    ]
