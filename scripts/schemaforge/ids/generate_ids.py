"""
SchemaForge IDS Pipeline — generate_ids.py
===========================================
Entry point for IDS generation from the GraphDB semantic graph.

Usage:
    cd /home/Dave/.openclaw/workspace-datadict
    PYTHONPATH=scripts/schemaforge python3 scripts/schemaforge/ids/generate_ids.py

Generates:
    SchemaForge_output/ids/KBOB_Raum.ids
    SchemaForge_output/ids/KBOB_Raum_summary.md

Architecture:
    GraphDB SPARQL → graph_retriever → ids_mapper → ids_builder → ids_writer → *.ids

Step 9 prototype: KBOB Raum / IfcSpace
  Applicability: IfcSpace
  Requirements:
    - CH_Space / sia-416-2003-label (required, enumeration)
    - CH_Space / sia-416-2003-code  (required, enumeration)
    - Pset_SpaceCommon / IsExternal (required, enumeration: true/false)
"""

import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE / "scripts" / "schemaforge"))

from ids.graph_retriever import (
    get_dictionary_spec,
    GRAPH_BDCH,
    GRAPH_KBOB,
)
from ids.ids_mapper import map_class_to_specification
from ids.ids_builder import build_ids
from ids.ids_writer import write_ids, write_ids_summary

# ── Targets ───────────────────────────────────────────────────────────────────
KBOB_RAUM_URI = "https://www.kbob.admin.ch/class/raum"

# Step 9 specified properties:
TARGET_PROPERTY_URIS = [
    "https://bauen-digital.ch/property/sia-416-2003-label",
    "https://bauen-digital.ch/property/sia-416-2003-code",
    "https://bauen-digital.ch/property/isexternal",
]

OUTPUT_DIR = WORKSPACE / "SchemaForge_output" / "ids"


def generate_kbob_raum_ids() -> None:
    print("=" * 70)
    print("SchemaForge IDS Generator — KBOB Raum / IfcSpace prototype")
    print("=" * 70)

    # ── 1. Retrieve semantic structures from GraphDB ──────────────────────────
    print("\n[1] Retrieving semantic graph from GraphDB...")
    spec = get_dictionary_spec(
        kbob_class_uri=KBOB_RAUM_URI,
        target_property_uris=TARGET_PROPERTY_URIS,
    )

    print(f"    KBOB class   : {spec.kbob_class.uri}")
    print(f"    IFC entity   : {spec.kbob_class.ifc_entity}")
    print(f"    bDCH mapping : {spec.bdch_class.uri if spec.bdch_class else 'NONE'}")
    print(f"    Properties   : {len(spec.properties)}")
    for p in spec.properties:
        avs = len(p.allowed_values)
        print(f"      - {p.uri.split('/')[-1]} [{p.data_type}] "
              f"pset={p.pset_name} required={p.is_required} "
              f"allowedValues={avs}")

    # ── 2. Map to IDS structures ──────────────────────────────────────────────
    print("\n[2] Mapping semantics to IDS structures...")
    ids_spec = map_class_to_specification(
        kbob_class=spec.kbob_class,
        bdch_class=spec.bdch_class,
        properties=spec.properties,
        spec_name="KBOB Raum — IfcSpace Requirements (CH_Space + Pset_SpaceCommon)",
    )
    print(f"    Specification: '{ids_spec.spec_name}'")
    print(f"    Entity       : {ids_spec.ifc_entity}")
    print(f"    Requirements : {len(ids_spec.properties)}")
    for p in ids_spec.properties:
        print(f"      - {p.pset_name}/{p.base_name} [{p.data_type}] "
              f"[{p.cardinality}] enum={len(p.enumeration)} values")

    # ── 3. Build IDS document ─────────────────────────────────────────────────
    print("\n[3] Building IDS document...")
    ids_doc = build_ids(
        spec_list=[ids_spec],
        title="KBOB Raum",
        version="0.1.0",
        description=(
            "IDS prototype: KBOB Raum class mapped to IfcSpace. "
            "Requires CH_Space properties (SIA 416 floor area type) "
            "and Pset_SpaceCommon/IsExternal from bDCH semantic graph."
        ),
        author="datadict@he-sem.ch",
        purpose="BIM data quality validation — PoC prototype",
    )
    print(f"    IDS title    : {ids_doc.info.get('title', 'n/a')}")
    print(f"    Specifications: {len(ids_doc.specifications)}")

    # ── 4. Write and validate IDS XML ─────────────────────────────────────────
    ids_output  = OUTPUT_DIR / "KBOB_Raum.ids"
    md_output   = OUTPUT_DIR / "KBOB_Raum_summary.md"

    print(f"\n[4] Writing IDS XML to: {ids_output}")
    written = write_ids(ids_doc, ids_output, validate=True)
    size = written.stat().st_size
    print(f"    Written: {written} ({size:,} bytes)")

    print(f"\n[5] Writing Markdown summary to: {md_output}")
    write_ids_summary(ids_doc, md_output)
    print(f"    Written: {md_output}")

    print("\n" + "=" * 70)
    print("✅  IDS generation complete.")
    print(f"    Output : {ids_output}")
    print(f"    Summary: {md_output}")
    print("=" * 70)


if __name__ == "__main__":
    generate_kbob_raum_ids()
