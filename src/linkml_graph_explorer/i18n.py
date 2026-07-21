"""Translation support based on GNU gettext.

The message catalog lives in ``locale/<lang>/LC_MESSAGES/`` inside the
package. English is the source language; unknown languages fall back to it.
The language is chosen by explicit argument, else the ``LGE_LANGUAGE``
environment variable, else English.
"""

from __future__ import annotations

import gettext
import os
from collections.abc import Callable
from importlib import resources

DOMAIN = "linkml_graph_explorer"
LANGUAGE_ENV_VAR = "LGE_LANGUAGE"
DEFAULT_LANGUAGE = "en"

Translator = Callable[[str], str]


def resolve_language(language: str | None = None) -> str:
    return language or os.environ.get(LANGUAGE_ENV_VAR) or DEFAULT_LANGUAGE


def translator(language: str | None = None) -> Translator:
    locale_dir = resources.files(__package__).joinpath("locale")
    translation = gettext.translation(
        DOMAIN,
        localedir=str(locale_dir),
        languages=[resolve_language(language)],
        fallback=True,
    )
    return translation.gettext
