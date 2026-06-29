"""
SchemaForge IDS Pipeline — ids_writer.py
=========================================
Serialises an ifctester Ids object to a valid IDS XML file.
Optionally validates the output against the official buildingSMART IDS XSD.

Architecture:
    ifctester.ids.Ids → ids_writer → *.ids (XML)
"""

import os
from pathlib import Path
from ifctester import ids as ifctester_ids


def write_ids(
    ids_doc: ifctester_ids.Ids,
    output_path: str | Path,
    validate: bool = True,
) -> Path:
    """
    Serialise the Ids document to a file at output_path.

    Args:
        ids_doc:     Built ifctester.ids.Ids object.
        output_path: Target file path (e.g. SchemaForge_output/ids/KBOB_Raum.ids).
        validate:    If True, validate the XML against the official IDS XSD before writing.

    Returns:
        Resolved Path to the written file.

    Raises:
        ifctester.ids.IdsXmlValidationError: if validate=True and the XML is invalid.
        IOError: if the file cannot be written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Serialise to XML string first (so we can validate before writing)
    xml_str = ids_doc.to_string()

    if validate:
        # ifctester validates against bundled IDS XSD on to_string();
        # additionally try a parse-back round-trip for schema conformance.
        try:
            roundtrip = ifctester_ids.from_string(xml_str)
            assert roundtrip.specifications, "Round-trip produced no specifications"
        except Exception as exc:
            raise ifctester_ids.IdsXmlValidationError(
                f"IDS round-trip validation failed: {exc}"
            ) from exc

    output_path.write_text(xml_str, encoding="utf-8")
    return output_path


def write_ids_summary(ids_doc: ifctester_ids.Ids, output_path: str | Path) -> None:
    """
    Write a human-readable Markdown summary of what was generated.
    Useful for worklog / documentation.
    """
    output_path = Path(output_path)
    info = ids_doc.info or {}
    lines = [
        f"# IDS Generation Summary: {info.get('title', 'Untitled')}",
        f"",
        f"- **Version:** {info.get('version', 'n/a')}",
        f"- **Description:** {info.get('description', 'n/a')}",
        f"- **Author:** {info.get('author', 'n/a')}",
        f"- **Specifications:** {len(ids_doc.specifications)}",
        f"",
    ]
    for spec in ids_doc.specifications:
        entity_names = [
            f.name if hasattr(f, "name") else str(f)
            for f in spec.applicability
            if isinstance(f, ifctester_ids.Entity)
        ]
        n_req = len(spec.requirements)
        lines.append(f"## {spec.name}")
        lines.append(f"- Applicability: {', '.join(entity_names)}")
        lines.append(f"- Requirements: {n_req} property facets")
        lines.append("")
        for req in spec.requirements:
            if isinstance(req, ifctester_ids.Property):
                pset  = req.propertySet if hasattr(req, "propertySet") else "?"
                bname = req.baseName    if hasattr(req, "baseName")    else "?"
                card  = req.cardinality if hasattr(req, "cardinality") else "?"
                has_enum = req.value is not None
                lines.append(
                    f"  - `{pset}` / `{bname}` "
                    f"[{card}]"
                    + (" [enumeration]" if has_enum else "")
                )
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
