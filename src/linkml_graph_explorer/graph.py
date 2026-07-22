"""Schema-driven derivation of graph elements from LinkML instance data.

Object-valued slots become directed edges labeled with the slot name.
Inlined instances (at any nesting depth) become nodes of their own, linked
to their containing instance by a containment edge. Only classes with an
identifier slot become nodes. Literal-valued slots feed the node detail
text shown on mouse-over.
"""

from __future__ import annotations

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SlotDefinition

from .viz_config import PARENT, VizConfig


def build_elements(
    schema_view: SchemaView,
    root_object: dict,
    root_class: str,
    config: VizConfig,
) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []

    for member_class, instance, parent in _occurrences(
        schema_view, root_object, root_class
    ):
        nodes.append(_node_for(schema_view, member_class, instance, config))
        edges.extend(_reference_edges(schema_view, member_class, instance))
        if parent is not None:
            edges.append(_containment_edge(schema_view, member_class,
                                           instance, parent))
        if member_class in config.collapse:
            edges.extend(_derived_edge(schema_view, member_class,
                                       instance, parent, config))

    return {"nodes": nodes, "edges": _drop_dangling(edges, nodes)}


def _occurrences(
    schema_view: SchemaView,
    instance: dict,
    class_name: str,
    parent: tuple[str, str] | None = None,
):
    """Yield (class_name, instance, parent) depth-first.

    ``parent`` is ``(parent_node_id, slot_name)`` for inlined instances
    whose container is itself a node, otherwise ``None``.
    """
    node_id = _identifier_or_none(schema_view, class_name, instance)
    if node_id is not None:
        yield class_name, instance, parent

    for slot in schema_view.class_induced_slots(class_name):
        child_class = _range_class(schema_view, slot)
        if child_class is None:
            continue
        child_parent = (node_id, slot.name) if node_id is not None else None
        for child in _inlined_instances(schema_view, child_class,
                                        instance.get(slot.name)):
            yield from _occurrences(schema_view, child, child_class,
                                    child_parent)


def _inlined_instances(
    schema_view: SchemaView, class_name: str, value
) -> list[dict]:
    """Normalize a slot value to its inlined instances.

    Handles single objects, ``inlined_as_list`` lists, and the compact
    dict form keyed by identifier. Scalar references are not instances
    and yield nothing here.
    """
    if isinstance(value, dict):
        id_slot = schema_view.get_identifier_slot(class_name)
        if id_slot is not None and id_slot.name in value:
            return [value]
        return [
            {id_slot.name: key, **entry} if id_slot else entry
            for key, entry in value.items()
            if isinstance(entry, dict)
        ]
    if isinstance(value, list):
        return [entry for entry in value if isinstance(entry, dict)]
    return []


def _reference_values(value) -> list[str]:
    """Normalize a slot value to its scalar references."""
    entries = value if isinstance(value, list) else [value]
    return [str(entry) for entry in entries
            if entry is not None and not isinstance(entry, dict)]


def _node_for(
    schema_view: SchemaView, member_class: str, instance: dict, config: VizConfig
) -> dict:
    identifier = _identifier_or_none(schema_view, member_class, instance)
    node = {"data": {
        "id": identifier,
        "label": instance.get(config.label_slot, identifier),
        "type": member_class,
        "detail": _detail_text(schema_view, member_class, instance, config),
    }}
    if member_class in config.collapse:
        node["classes"] = "reified"
    return node


def _reference_edges(
    schema_view: SchemaView, member_class: str, instance: dict
):
    source = _identifier_or_none(schema_view, member_class, instance)
    for slot in schema_view.class_induced_slots(member_class):
        if _range_class(schema_view, slot) is None:
            continue
        for target in _reference_values(instance.get(slot.name)):
            yield {"data": {
                "id": f"{source}--{slot.name}--{target}",
                "source": source,
                "target": target,
                "label": slot.name,
                "detail": (slot.description or slot.name).strip(),
            }}


def _containment_edge(
    schema_view: SchemaView,
    member_class: str,
    instance: dict,
    parent: tuple[str, str],
) -> dict:
    parent_id, slot_name = parent
    node_id = _identifier_or_none(schema_view, member_class, instance)
    slot = schema_view.get_slot(slot_name)
    return {"data": {
        "id": f"{parent_id}--{slot_name}--{node_id}",
        "source": parent_id,
        "target": node_id,
        "label": slot_name,
        "detail": ((slot and slot.description) or slot_name).strip(),
    }}


def _derived_edge(
    schema_view: SchemaView,
    member_class: str,
    instance: dict,
    parent: tuple[str, str] | None,
    config: VizConfig,
):
    rule = config.collapse[member_class]
    source = (parent[0] if parent else None) if rule.source_slot == PARENT \
        else instance.get(rule.source_slot)
    target = instance.get(rule.target_slot)
    if source is None or target is None:
        return
    identifier = _identifier_or_none(schema_view, member_class, instance)
    yield {
        "data": {
            "id": f"{identifier}--collapsed",
            "source": str(source),
            "target": str(target),
            "label": instance.get(config.label_slot, identifier),
            "detail": _detail_text(schema_view, member_class, instance, config),
            "relation": member_class,
        },
        "classes": "derived",
    }


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


def _identifier_or_none(
    schema_view: SchemaView, class_name: str, instance: dict
) -> str | None:
    id_slot = schema_view.get_identifier_slot(class_name)
    if id_slot is None or id_slot.name not in instance:
        return None
    return str(instance[id_slot.name])


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
