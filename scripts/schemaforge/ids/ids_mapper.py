"""
SchemaForge IDS Pipeline — ids_mapper.py
=========================================
Defines the explicit RDF-semantic → IDS transformation rules.

Mapping table (per task spec §2):
─────────────────────────────────────────────────────────────────────────────
RDF Semantic Structure          │ IDS Structure
────────────────────────────────┼────────────────────────────────────────────
hesem:ifcEntityCode             │ <applicability><entity><name>
hesem:ifcPredefinedType         │ <applicability><entity><predefinedType>
hesem:propertySetName (on Assign)│ <propertySet><simpleValue>
hesem:ifcPsetUri                │ IDS uri attribute on <propertySet>
rdfs:label (prop)               │ <baseName><simpleValue>
hesem:ifcPropertyUri            │ IDS uri attribute on <baseName>
hesem:dataType                  │ <dataType> (mapped to IFC schema type)
hesem:hasAllowedValue → valueCode│ <value><restriction> enumeration
hesem:isRequired = true         │ cardinality="required"
hesem:isRequired = false        │ cardinality="optional"
Assignment URI                  │ Traceability comment in <instructions>
─────────────────────────────────────────────────────────────────────────────

Design principles:
- Mapping is explicit and data-driven; no implicit defaults.
- BOOLEAN allowed values are normalised to lowercase "true"/"false".
- Unknown datatypes fall back to IFCLABEL (safe for string-typed props).
- Each mapping decision is documented in-line.
"""

from dataclasses import dataclass, field
from typing import Optional

from .graph_retriever import PropertyInfo, ClassInfo


# ── Datatype mapping: HE-SEM → IFC schema type string ─────────────────────────
# IDS expects IFC EXPRESS type names, e.g. IFCLABEL, IFCBOOLEAN, IFCREAL.
HESEM_TO_IFC_TYPE: dict[str, str] = {
    "STRING":   "IFCLABEL",
    "BOOLEAN":  "IFCBOOLEAN",
    "INTEGER":  "IFCINTEGER",
    "REAL":     "IFCREAL",
    "TIME":     "IFCDATE",
    "DATETIME": "IFCDATETIME",
}


@dataclass
class IDSPropertySpec:
    """IDS-ready representation of a single property requirement."""
    pset_name: str                           # PropertySet name for IDS
    pset_uri: Optional[str]                  # PropertySet IRI (for IDS uri attribute)
    base_name: str                           # Property name for IDS
    base_name_uri: Optional[str]             # Property IRI (for IDS uri attribute)
    data_type: str                           # IFC schema type, e.g. IFCLABEL
    cardinality: str                         # "required" or "optional"
    enumeration: list[str]                   # Allowed values (empty = no restriction)
    instructions: Optional[str]             # Traceability: source Assignment URI + property URI


@dataclass
class IDSSpecificationSpec:
    """IDS-ready representation of one complete Specification (applicability + requirements)."""
    spec_name: str
    ifc_entity: str
    ifc_predefined_type: Optional[str]
    properties: list[IDSPropertySpec] = field(default_factory=list)
    description: Optional[str] = None


def map_datatype(hesem_type: str) -> str:
    """Map a HE-SEM datatype string to an IFC schema type string."""
    return HESEM_TO_IFC_TYPE.get(hesem_type.upper(), "IFCLABEL")


def _normalize_boolean_values(values: list[str]) -> list[str]:
    """
    Normalise BOOLEAN allowed values to lowercase "true"/"false".
    IDS validators expect lowercase boolean literals.
    """
    normalised = []
    for v in values:
        vl = v.strip().lower()
        if vl in ("true", "1", "yes"):
            normalised.append("true")
        elif vl in ("false", "0", "no"):
            normalised.append("false")
        else:
            normalised.append(vl)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for v in normalised:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def map_property(prop: PropertyInfo) -> IDSPropertySpec:
    """
    Transform a PropertyInfo (from graph_retriever) into an IDSPropertySpec.

    Rules:
    - pset_name: use hesem:propertySetName from Assignment; fall back to property URI fragment.
    - base_name: use rdfs:label (de or en) from property resource.
      Note: IDS baseName must match the IFC property name exactly.
      If ifcPropertyUri is available, the actual IFC property name is derived from it.
    - data_type: mapped via HESEM_TO_IFC_TYPE.
    - enumeration: collect valueCode values; normalise BOOLEANs.
    - cardinality: "required" if isRequired=true, else "optional".
    - instructions: traceability string pointing to Assignment URI and property URI.
    """
    # Determine property name for IDS:
    # Priority 1: IFC property URI fragment → canonical IFC name.
    #   e.g. .../prop/IsExternal → "IsExternal"
    # Priority 2: property URI slug (last path segment).
    #   e.g. .../property/sia-416-2003-label → "sia-416-2003-label"
    #   This is the best identifier for custom pset properties not in bSDD.
    # Priority 3: rdfs:label (last resort, locale-dependent).
    if prop.ifc_prop_uri:
        base_name = prop.ifc_prop_uri.rstrip("/").split("/")[-1]
    elif prop.uri:
        base_name = prop.uri.rstrip("/").split("/")[-1]
    else:
        base_name = prop.label

    # PropertySet name: prefer assignment-level pset name
    pset_name = prop.pset_name or "UnknownPset"

    ifc_type = map_datatype(prop.data_type)

    # Collect and normalise allowed values
    raw_values = [av.code for av in prop.allowed_values]
    if ifc_type == "IFCBOOLEAN":
        enum_values = _normalize_boolean_values(raw_values)
    else:
        enum_values = raw_values

    cardinality = "required" if prop.is_required else "optional"

    instructions = (
        f"Source: {prop.assign_uri or 'unknown'} | "
        f"Property: {prop.uri} | "
        f"DataType: {prop.data_type}"
    )

    return IDSPropertySpec(
        pset_name=pset_name,
        pset_uri=prop.ifc_pset_uri,
        base_name=base_name,
        base_name_uri=prop.ifc_prop_uri,
        data_type=ifc_type,
        cardinality=cardinality,
        enumeration=enum_values,
        instructions=instructions,
    )


def map_class_to_specification(
    kbob_class: ClassInfo,
    bdch_class: Optional[ClassInfo],
    properties: list[PropertyInfo],
    spec_name: Optional[str] = None,
) -> IDSSpecificationSpec:
    """
    Build an IDSSpecificationSpec from class info + property list.

    Applicability:
    - IFC entity comes from kbob_class.ifc_entity (e.g. "IfcSpace")
    - PredefinedType from kbob_class.ifc_predefined_type (if set)

    Requirements:
    - One IDSPropertySpec per PropertyInfo.

    Description:
    - Semantic chain: KBOB class → bDCH class (SKOS match) → properties
    """
    if spec_name is None:
        spec_name = f"{kbob_class.label} — IFC Requirements"

    bdch_label = bdch_class.label if bdch_class else "n/a"
    bdch_uri   = bdch_class.uri   if bdch_class else "n/a"

    description = (
        f"KBOB Raum: {kbob_class.uri} | "
        f"bDCH mapping: {bdch_uri} ({bdch_label}) | "
        f"IFC entity: {kbob_class.ifc_entity}"
    )

    mapped_props = [map_property(p) for p in properties]

    return IDSSpecificationSpec(
        spec_name=spec_name,
        ifc_entity=kbob_class.ifc_entity,
        ifc_predefined_type=kbob_class.ifc_predefined_type,
        properties=mapped_props,
        description=description,
    )
