"""Document rendering of instance data via linkml-renderer."""

from __future__ import annotations

from pathlib import Path

import yaml
from linkml_runtime import SchemaView
from linkml_renderer.renderers.html_renderer import HTMLRenderer
from linkml_renderer.renderers.markdown_renderer import MarkdownRenderer
from linkml_renderer.renderers.mermaid_renderer import MermaidRenderer
from linkml_renderer.style.style_engine import StyleEngine

RENDERERS = {
    "html": (HTMLRenderer, ".html"),
    "markdown": (MarkdownRenderer, ".md"),
    "mermaid": (MermaidRenderer, ".mermaid"),
}


def render_docs(
    schema_path: Path,
    data_path: Path,
    out_dir: Path,
    root_class: str,
    formats: tuple[str, ...] = ("html", "markdown"),
) -> list[Path]:
    unknown = [name for name in formats if name not in RENDERERS]
    if unknown:
        raise ValueError(f"unknown formats {unknown}, allowed: {sorted(RENDERERS)}")

    schema_view = SchemaView(str(schema_path))
    root_object = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for name in formats:
        renderer_class, suffix = RENDERERS[name]
        renderer = renderer_class()
        renderer.style_engine = StyleEngine(schema_view)
        rendered = renderer.render(
            root_object, schema_view, source_element_name=root_class
        )
        target = out_dir / f"{data_path.stem}{suffix}"
        target.write_text(rendered, encoding="utf-8")
        written.append(target)
    return written
