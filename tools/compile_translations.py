#!/usr/bin/env python3
"""Compile all .po files under src/**/locale into binary .mo files.

Pure standard library, so translators and CI do not need the GNU gettext
toolchain. Usage: python tools/compile_translations.py
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_po(path: Path) -> dict[str, str]:
    catalog: dict[str, str] = {}
    msgid: list[str] = []
    msgstr: list[str] = []
    section: list[str] | None = None

    def flush() -> None:
        if section is not None and msgid:
            catalog["".join(msgid)] = "".join(msgstr)

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            flush()
            msgid = [_unquote(line[len("msgid "):])]
            msgstr = []
            section = msgid
        elif line.startswith("msgstr "):
            msgstr = [_unquote(line[len("msgstr "):])]
            section = msgstr
        elif line.startswith('"') and section is not None:
            section.append(_unquote(line))
    flush()
    return catalog


def _unquote(fragment: str) -> str:
    if not (fragment.startswith('"') and fragment.endswith('"')):
        raise ValueError(f"malformed .po fragment: {fragment!r}")
    return (
        fragment[1:-1]
        .replace(r"\n", "\n")
        .replace(r"\t", "\t")
        .replace(r"\"", '"')
        .replace(r"\\", "\\")
    )


def write_mo(catalog: dict[str, str], path: Path) -> None:
    entries = sorted(
        (key.encode("utf-8"), value.encode("utf-8"))
        for key, value in catalog.items()
    )

    key_blob = b""
    value_blob = b""
    key_index: list[tuple[int, int]] = []
    value_index: list[tuple[int, int]] = []
    for key, value in entries:
        key_index.append((len(key), len(key_blob)))
        value_index.append((len(value), len(value_blob)))
        key_blob += key + b"\0"
        value_blob += value + b"\0"

    count = len(entries)
    header_size = 7 * 4
    key_table_offset = header_size
    value_table_offset = key_table_offset + count * 8
    key_blob_offset = value_table_offset + count * 8
    value_blob_offset = key_blob_offset + len(key_blob)

    header = struct.pack(
        "<7I",
        0x950412DE,
        0,
        count,
        key_table_offset,
        value_table_offset,
        0,
        0,
    )
    key_table = b"".join(
        struct.pack("<2I", length, key_blob_offset + offset)
        for length, offset in key_index
    )
    value_table = b"".join(
        struct.pack("<2I", length, value_blob_offset + offset)
        for length, offset in value_index
    )
    path.write_bytes(header + key_table + value_table + key_blob + value_blob)


def main() -> int:
    po_files = sorted(PROJECT_ROOT.glob("src/**/locale/**/*.po"))
    if not po_files:
        print("no .po files found", file=sys.stderr)
        return 1
    for po_file in po_files:
        mo_file = po_file.with_suffix(".mo")
        write_mo(parse_po(po_file), mo_file)
        print(f"compiled {po_file.relative_to(PROJECT_ROOT)} -> "
              f"{mo_file.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
