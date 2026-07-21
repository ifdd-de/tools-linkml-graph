import pytest

from linkml_graph_explorer.docs import render_docs


def test_renders_html_and_markdown(schema_path, data_path, tmp_path):
    written = render_docs(schema_path, data_path, tmp_path, "GridModel")
    names = {path.name for path in written}
    assert names == {"circuit_sunville.html", "circuit_sunville.md"}
    markdown = (tmp_path / "circuit_sunville.md").read_text(encoding="utf-8")
    assert "Transformer T1" in markdown


def test_renders_mermaid_on_request(schema_path, data_path, tmp_path):
    written = render_docs(
        schema_path, data_path, tmp_path, "GridModel", ("mermaid",)
    )
    assert written[0].suffix == ".mermaid"


def test_unknown_format_is_rejected(schema_path, data_path, tmp_path):
    with pytest.raises(ValueError, match="pptx"):
        render_docs(schema_path, data_path, tmp_path, "GridModel", ("pptx",))
