import json

from click.testing import CliRunner

from linkml_graph_explorer.cli import main


def run(*args, env=None):
    return CliRunner().invoke(main, list(args), env=env, catch_exceptions=False)


def test_all_writes_three_files(tmp_path):
    result = run("all", "--out", str(tmp_path))
    assert result.exit_code == 0
    names = {path.name for path in tmp_path.iterdir()}
    assert names == {
        "circuit_sunville.html",
        "circuit_sunville.md",
        "circuit_sunville_explorer.html",
    }


def test_graph_accepts_positions_file(tmp_path):
    layout_file = tmp_path / "layout.json"
    layout_file.write_text(
        json.dumps({"positions": {"SUB-SNV": {"x": 0, "y": 0}}}),
        encoding="utf-8",
    )
    result = run("graph", "--out", str(tmp_path),
                 "--positions", str(layout_file))
    assert result.exit_code == 0
    html = (tmp_path / "circuit_sunville_explorer.html").read_text("utf-8")
    assert "SUB-SNV" in html


def test_language_option_switches_message(tmp_path):
    result = run("graph", "--out", str(tmp_path), "--language", "de")
    assert result.output.startswith("geschrieben: ")


def test_language_env_var_switches_message(tmp_path):
    result = run("graph", "--out", str(tmp_path), env={"LGE_LANGUAGE": "de"})
    assert result.output.startswith("geschrieben: ")


def test_default_language_is_english(tmp_path):
    result = run("graph", "--out", str(tmp_path))
    assert result.output.startswith("wrote ")
