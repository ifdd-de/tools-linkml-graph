"""Command line interface. Purely file based, no running services."""

from __future__ import annotations

from pathlib import Path

import click

from .docs import render_docs
from .explorer import render_explorer_html
from .i18n import LANGUAGE_ENV_VAR, translator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = PROJECT_ROOT / "schema" / "grid_assets.yaml"
DEFAULT_DATA = PROJECT_ROOT / "data" / "circuit_sunville.yaml"
DEFAULT_VIZ_CONFIG = PROJECT_ROOT / "config" / "viz.yaml"
DEFAULT_ROOT_CLASS = "GridModel"

common_options = [
    click.option("--schema", "schema_path",
                 type=click.Path(exists=True, path_type=Path),
                 default=DEFAULT_SCHEMA, show_default=True,
                 help="LinkML schema file."),
    click.option("--data", "data_path",
                 type=click.Path(exists=True, path_type=Path),
                 default=DEFAULT_DATA, show_default=True,
                 help="Instance data (YAML)."),
    click.option("--out", "out_dir", type=click.Path(path_type=Path),
                 default=Path("output"), show_default=True,
                 help="Output directory."),
    click.option("--root", "root_class", default=DEFAULT_ROOT_CLASS,
                 show_default=True,
                 help="Root class (tree_root) of the instance data."),
    click.option("--language", "-l", "language",
                 type=click.Choice(["en", "de"]), default=None,
                 envvar=LANGUAGE_ENV_VAR,
                 help="Output language (also via env var "
                      f"{LANGUAGE_ENV_VAR})."),
]

viz_config_option = click.option(
    "--viz-config", "viz_config_path",
    type=click.Path(exists=True, path_type=Path),
    default=DEFAULT_VIZ_CONFIG, show_default=True,
    help="Visualization configuration (YAML), validated against the schema.")

positions_option = click.option(
    "--positions", "positions_path",
    type=click.Path(exists=True, path_type=Path), default=None,
    help="Layout file previously saved in the browser; "
         "baked in as a deterministic preset layout.")


def apply(options):
    def decorator(command):
        for option in reversed(options):
            command = option(command)
        return command
    return decorator


def echo_written(paths: list[Path], language: str | None) -> None:
    _ = translator(language)
    for path in paths:
        click.echo(_("wrote {path}").format(path=path))


@click.group()
@click.version_option(package_name="linkml-graph-explorer")
def main() -> None:
    """Render LinkML instance data as documents and exploration graphs."""


@main.command()
@apply(common_options)
@click.option("--formats", default="html,markdown", show_default=True,
              help="Comma separated: html, markdown, mermaid.")
def docs(schema_path: Path, data_path: Path, out_dir: Path, root_class: str,
         language: str | None, formats: str) -> None:
    """Render instance data via linkml-renderer."""
    selected = tuple(name.strip() for name in formats.split(",") if name.strip())
    written = render_docs(schema_path, data_path, out_dir, root_class, selected)
    echo_written(written, language)


@main.command()
@apply(common_options)
@viz_config_option
@positions_option
def graph(schema_path: Path, data_path: Path, out_dir: Path, root_class: str,
          language: str | None, viz_config_path: Path,
          positions_path: Path | None) -> None:
    """Create the standalone exploration HTML (offline capable)."""
    target = render_explorer_html(
        schema_path, data_path, viz_config_path, out_dir, root_class,
        positions_path=positions_path, language=language,
    )
    echo_written([target], language)


@main.command(name="all")
@apply(common_options)
@viz_config_option
@positions_option
def render_all(schema_path: Path, data_path: Path, out_dir: Path,
               root_class: str, language: str | None, viz_config_path: Path,
               positions_path: Path | None) -> None:
    """Create all render targets in one run."""
    written = render_docs(schema_path, data_path, out_dir, root_class,
                          ("html", "markdown"))
    written.append(render_explorer_html(
        schema_path, data_path, viz_config_path, out_dir, root_class,
        positions_path=positions_path, language=language,
    ))
    echo_written(written, language)


if __name__ == "__main__":
    main()
