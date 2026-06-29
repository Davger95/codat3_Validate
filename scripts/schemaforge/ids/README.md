# SchemaForge IDS Generation Pipeline

## Architecture

```
Excel DD → RDF/TriG → GraphDB → IDS Generator → IDS XML
```

The RDF semantic graph is the **single authoritative source**. IDS generation is a semantic transformation — no Excel re-parsing.

```
GraphDB SPARQL
  ↓
graph_retriever.py     — queries named graphs, returns typed dataclasses
  ↓
ids_mapper.py          — explicit RDF → IDS transformation rules
  ↓
ids_builder.py         — assembles ifctester.ids.Ids objects
  ↓
ids_writer.py          — serialises to IDS XML + Markdown summary
  ↓
*.ids                  — valid IDS XML (XSD-validated)
```

## Module Overview

| Module | Role |
|--------|------|
| `graph_retriever.py` | SPARQL → Python dataclasses. GraphDB SSH + named graph queries. |
| `ids_mapper.py` | RDF predicate → IDS facet mapping. Explicit, documented transformation rules. |
| `ids_builder.py` | Assembles ifctester `Ids` + `Specification` + `Property` objects. |
| `ids_writer.py` | Serialises to `.ids` XML. Validates via round-trip + XSD. |
| `generate_ids.py` | Entry point for the KBOB Raum / IfcSpace prototype. |

## Semantic-to-IDS Mapping Table

| RDF Predicate / Structure | IDS Element |
|--------------------------|-------------|
| `hesem:ifcEntityCode` | `<entity><name>` in applicability |
| `hesem:ifcPredefinedType` | `<entity><predefinedType>` in applicability |
| `hesem:propertySetName` (on Assignment) | `<propertySet><simpleValue>` |
| `hesem:ifcPsetUri` | `uri` attribute on `<propertySet>` *(future)* |
| `rdfs:label` / URI slug (prop) | `<baseName><simpleValue>` |
| `hesem:ifcPropertyUri` | `uri` attribute on property + canonical IFC name |
| `hesem:dataType` | `@dataType` (mapped STRING→IFCLABEL, BOOLEAN→IFCBOOLEAN, …) |
| `hesem:hasAllowedValue → valueCode` | `<value><xs:restriction><xs:enumeration>` |
| `hesem:isRequired = true` | `@cardinality="required"` |
| `hesem:isRequired = false` | `@cardinality="optional"` |
| Assignment URI | `@instructions` (traceability) |

## Datatype Mapping

| HE-SEM Type | IFC Schema Type |
|-------------|----------------|
| STRING | IFCLABEL |
| BOOLEAN | IFCBOOLEAN |
| INTEGER | IFCINTEGER |
| REAL | IFCREAL |
| TIME | IFCDATE |
| DATETIME | IFCDATETIME |

## SPARQL Retrieval Strategy

All queries target named graphs:
- `https://www.kbob.admin.ch/graph/dd` — KBOB dictionary
- `https://bauen-digital.ch/graph/dd` — bDCH dictionary
- `https://he-sem.ch/graph/mappings` — cross-dictionary SKOS mappings

Semantic chain for KBOB Raum:
1. Retrieve KBOB class: `hesem:ifcEntityCode`, `hesem:ifcPredefinedType`
2. Follow SKOS (`closeMatch` / `exactMatch` / `broadMatch`) to bDCH class
3. Retrieve all `hesem:Assignment` nodes for the bDCH class
4. Per Assignment: `hesem:assignedProperty`, `hesem:isRequired`, `hesem:propertySetName`, `hesem:propertySet`
5. Per Property: `hesem:dataType`, `hesem:ifcPropertyUri`, `hesem:hasAllowedValue → hesem:valueCode`

Supports:
- Named graph filtering (by dictionary)
- Property subset filtering (`target_property_uris` parameter)
- Future: LOIN phase / use-case filtering via `hesem:loinSiaPhase`, `hesem:loinUseCase`

## Step 9 Prototype: KBOB Raum / IfcSpace

Entry point: `generate_ids.py`

```bash
cd /home/Dave/.openclaw/workspace-datadict
PYTHONPATH=scripts/schemaforge python3 scripts/schemaforge/ids/generate_ids.py
```

Output:
- `SchemaForge_output/ids/KBOB_Raum.ids` — valid IDS XML
- `SchemaForge_output/ids/KBOB_Raum_summary.md` — human-readable summary

Semantic chain resolved:
```
KBOB Raum (https://www.kbob.admin.ch/class/raum)
  skos:closeMatch →
bDCH aussen-nettogeschossflache (https://bauen-digital.ch/class/aussen-nettogeschossflache)
  hesem:Assignment →
    CH_Space / sia-416-2003-label  [IFCLABEL, required, 37 enumeration values]
    CH_Space / sia-416-2003-code   [IFCLABEL, required, 14 enumeration values]
    Pset_SpaceCommon / IsExternal  [IFCBOOLEAN, required, enum: true/false]
```

## SHACL ↔ IDS Relationship (Recommendation)

**Recommended architecture:** parallel outputs from the same RDF graph:

```
RDF Graph (GraphDB)
  ├── → SHACL shapes (validation of RDF data)
  └── → IDS XML     (IFC model validation)
```

**Rationale:**
- SHACL and IDS serve different validation contexts (RDF vs IFC).
- Both should be generated from the same semantic source to avoid drift.
- SHACL shapes validate the RDF graph itself; IDS validates IFC model files.
- A `shacl_writer.py` module should be implemented in parallel (see backlog).

**Do NOT do:** SHACL → IDS (lossy, adds indirection).

## Limitations (Current v0.1 Prototype)

1. **baseName for custom CH_Space properties** uses the URI slug (`sia-416-2003-label`). This must match the actual IFC PropertySet property name. Review against the CH_Space Pset specification.
2. **BOOLEAN enumerations** use string `"true"`/`"false"` — IDS validators differ on boolean facet handling.
3. **No LOIN filtering** yet — all assignments retrieved, not filtered by phase/role.
4. **No predefinedType** on KBOB Raum (data not populated).
5. **Class hierarchy** not yet reflected (ParentClassCode missing in source data).

## Future Extensions

- `generate_kbob_full.ids` — all KBOB classes
- `generate_bdch_full.ids` — all bDCH classes
- LOIN-filtered IDS by SIA phase or use case
- Subsystem-filtered IDS for railway
- SHACL writer parallel implementation
