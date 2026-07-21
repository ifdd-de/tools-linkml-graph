from linkml_graph_explorer.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_ENV_VAR,
    resolve_language,
    translator,
)


def test_english_is_the_source_language():
    assert translator("en")("Save layout") == "Save layout"


def test_german_catalog_is_applied():
    _ = translator("de")
    assert _("Save layout") == "Layout speichern"
    assert _("wrote {path}") == "geschrieben: {path}"


def test_unknown_language_falls_back_to_english():
    assert translator("fr")("Save layout") == "Save layout"


def test_language_resolution_order(monkeypatch):
    monkeypatch.delenv(LANGUAGE_ENV_VAR, raising=False)
    assert resolve_language(None) == DEFAULT_LANGUAGE
    monkeypatch.setenv(LANGUAGE_ENV_VAR, "de")
    assert resolve_language(None) == "de"
    assert resolve_language("en") == "en"
