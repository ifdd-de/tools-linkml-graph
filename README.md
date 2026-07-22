# linkml-graph-explorer

[![CI](https://github.com/mleist/linkml-graph-explorer/actions/workflows/ci.yml/badge.svg)](https://github.com/mleist/linkml-graph-explorer/actions/workflows/ci.yml)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-green.svg)](LICENSE)
![GitHub last commit](https://img.shields.io/github/last-commit/mleist/linkml-graph-explorer)

Render [LinkML](https://linkml.io/) instance data as documents
([linkml-renderer](https://github.com/linkml/linkml-renderer)) and as
**standalone interactive exploration graphs**
([Cytoscape.js](https://js.cytoscape.org/)) — driven entirely by the schema
and a separate visualization configuration. Purely CLI based, no running
services; all results are written as files to a local output directory.

The bundled example models a fictional transmission-grid domain: a 380 kV
circuit between the substations *Sunville* and *Loadstead*.

## How it works

The LinkML schema is the single structural authority:

- **Object-valued slots** (`range` = class with an identifier, e.g.
  `installed_at`, `from_location`) become **directed edges** labeled with
  the slot name; the slot `description` becomes the edge's mouse-over text.
- **Literal-valued slots** (`description`, `voltage_kv`, …) become node
  attributes that feed the detail-on-demand text.

Everything visual — colors, shapes, edge line styles, which slot provides
the label and which the detail text — lives in a separate
**visualization configuration** (`config/viz.yaml`). Every class and slot
name in that file is validated against the schema at load time; unknown
names fail fast with a clear error. Nothing about the rendering is
hard-coded: new classes or relations in the schema show up in the graph,
with per-class visibility toggles, without touching any Python code.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
python tools/compile_translations.py
```

Tested with Python 3.10/3.12, linkml-renderer 0.3.1 and Cytoscape.js 3.34.0
(bundled under `src/linkml_graph_explorer/vendor/`, MIT license, header
preserved).

## Usage

```bash
graph-explorer all   --out output                 # every render target
graph-explorer docs  --out output --formats html,markdown,mermaid
graph-explorer graph --out output                 # exploration HTML only

graph-explorer all --schema schema/grid_assets.yaml \
                   --data data/circuit_sunville.yaml \
                   --viz-config config/viz.yaml \
                   --root GridModel --out output
```

| Output file | Producer | Content |
|---|---|---|
| `circuit_sunville.html` | linkml-renderer | Tabular HTML view of the instance data |
| `circuit_sunville.md` | linkml-renderer | Markdown view |
| `circuit_sunville_explorer.html` | explorer | **Standalone** exploration graph: single file, works offline, node/edge tooltips, class toggles, switchable layout engines, compact view, default view/fit/zoom, layout save & load, PNG export |

## Visualization configuration

```yaml
label_slot: name          # slot used as node label
detail_slot: description  # slot shown first in the mouse-over text

defaults:
  node: { color: "#e5e7eb", shape: round-rectangle }
  edge: { color: "#9ca3af", line_style: solid }

classes:
  Location: { color: "#bbf7d0", shape: hexagon }
  Circuit:  { color: "#fde68a", shape: ellipse }

edges:
  part_of_circuit: { color: "#f59e0b", line_style: dashed }
```

Shapes and line styles are passed through to Cytoscape.js
(`round-rectangle`, `hexagon`, `ellipse`, …; `solid`, `dashed`, `dotted`).

### Layout engines

```yaml
layout:
  default: fcose
  engines:
    fcose:
      nodeDimensionsIncludeLabels: true
      idealEdgeLength: 70
      degreeScaledEdgeLength: true   # hub edges get longer edges
    elk:
      elk: { algorithm: layered, elk.direction: RIGHT }
```

Only the engines listed here are embedded into the standalone HTML, and a
toolbar dropdown switches between them at runtime. Measured impact on the
generated file: fcose adds roughly 0.3 MB, ELK roughly 1.6 MB (fcose-only
export ≈ 0.75 MB, both engines ≈ 2.3 MB). All options are passed through to
the engine unchanged, with one convenience extension: for fcose,
`degreeScaledEdgeLength: true` replaces `idealEdgeLength` by a per-edge
function that lengthens edges at high-degree nodes — this untangles the
typical hub fans of infrastructure graphs. `elk` options live in the nested
`elk` object using ELK's own option keys. Without a `layout` section the
default is a plain fcose. A layout file baked in via `--positions` still
wins as the initial and default view.

### Compact view (collapsing reified relations)

Domain models often reify relations as classes — in the example, `Circuit`
is exactly that: an object linking two locations. The `collapse` section
declares such classes and their endpoint slots:

```yaml
collapse:
  Circuit: { source_slot: from_location, target_slot: to_location }
```

The export then contains, in addition to the regular elements, one derived
edge per instance (styled in the class color, labeled with the instance
name, full detail text on mouse-over). A *Compact view* toolbar checkbox
switches between the reified representation and the contracted one; the
control only appears when `collapse` is configured. This is deliberately a
global toggle, not per-node plus/minus expanders: a reified relation
belongs to a *pair* of nodes, so there is no single node to anchor an
expander on — per-node expand/collapse is a hierarchy pattern and does not
apply to general (cyclic) association graphs.

## Layout: move, save, load

Nodes are freely draggable. The layout cycle is entirely file based:

1. Arrange nodes with the mouse, set zoom and pan.
2. *Save layout* downloads `<dataset>_layout.json` (positions, zoom, pan);
   this also works when the HTML is opened locally via `file://`.
3. *Load layout* reads such a file back in without regenerating the HTML.
4. Bake it in for a deterministic default view:

   ```bash
   graph-explorer graph --out output --positions my_layout.json
   ```

   The page then starts with a preset layout instead of the
   non-deterministic force layout, and *Default view* restores exactly it.

Nodes missing from the layout file start at the origin (0, 0) — after
schema or data extensions, rearrange once and save again.

## Image export

The *PNG* button downloads the currently visible viewport as a PNG
(2x scale, white background) via the native `cy.png()` core API — no
additional dependency. SVG export was evaluated and deliberately left out:
the only established extension, `cytoscape-svg`, is GPLv3-licensed, which
conflicts with distributing it inside this BSD-3-Clause project's
single-file HTML output. If you need SVG and can accept GPLv3 terms for
your own deployment, the extension can be added locally without code
changes to this project's Python side.

## Internationalization

The source language is English; a German catalog ships with the project.
Select the output language of CLI messages and of the UI strings in the
generated explorer HTML via `--language de` / `-l de` or the environment
variable `LGE_LANGUAGE=de`. Unknown languages fall back to English.
Developer-facing error messages intentionally stay English.

To add a language, copy
`src/linkml_graph_explorer/locale/linkml_graph_explorer.pot` to
`src/linkml_graph_explorer/locale/<lang>/LC_MESSAGES/linkml_graph_explorer.po`,
translate the `msgstr` entries, run `python tools/compile_translations.py`
(pure standard library, no gettext toolchain required), and add the language
code to the `--language` choice in `cli.py`.

## Development

```bash
pytest -q                                  # run the test suite
linkml-validate -s schema/grid_assets.yaml -C GridModel data/circuit_sunville.yaml
```

The `linkml` toolchain providing `linkml-validate` (and the `gen-*`
generators) is not a runtime dependency of the package; it is installed
via the `test` extra.

CI (GitHub Actions) compiles the translations and runs the test suite on
Python 3.10 and 3.12 for every push and pull request.

## Project layout

```
linkml-graph-explorer/
├── schema/grid_assets.yaml        # LinkML schema (structural authority)
├── data/circuit_sunville.yaml     # example instance data
├── config/viz.yaml                # visualization configuration
├── src/linkml_graph_explorer/
│   ├── cli.py                     # click CLI: docs | graph | all
│   ├── docs.py                    # linkml-renderer binding
│   ├── graph.py                   # schema-driven element derivation
│   ├── explorer.py                # stylesheet generation + HTML assembly
│   ├── viz_config.py              # config loading + schema validation
│   ├── i18n.py                    # gettext-based translation
│   ├── template.html              # explorer template (placeholders)
│   ├── locale/                    # .pot template, per-language .po/.mo
│   └── vendor/                    # Cytoscape.js (MIT), fcose stack (MIT),
│                                  #   cytoscape-elk (MIT), elkjs (EPL-2.0)
├── tests/                         # pytest suite covering all modules
└── tools/compile_translations.py  # stdlib .po -> .mo compiler
```

## License

BSD 3-Clause, see [LICENSE](LICENSE). Bundled third-party components keep
their own licenses in `src/linkml_graph_explorer/vendor/`: Cytoscape.js,
cytoscape-fcose (with layout-base/cose-base) and cytoscape-elk are MIT;
elkjs is EPL-2.0.
