"""
SchemaForge IDS Pipeline — ids_builder.py
==========================================
Assembles ifctester Ids objects from IDSSpecificationSpec structures.
Uses the ifctester 0.8.x Python API (buildingSMART official library).

Architecture:
    IDSSpecificationSpec → ifctester.ids.Ids → ids_writer
"""

from ifctester import ids as ifctester_ids
from .ids_mapper import IDSSpecificationSpec, IDSPropertySpec


# ── IFC version used throughout ───────────────────────────────────────────────
IFC_VERSION = ["IFC4X3_ADD2"]


def _build_property_facet(prop_spec: IDSPropertySpec) -> ifctester_ids.Property:
    """
    Build one ifctester Property facet from an IDSPropertySpec.

    - If enumeration is non-empty → Restriction with enumeration
    - If enumeration is empty    → no value restriction (any value accepted)
    - pset_uri / base_name_uri   → uri attributes on PropertySet / BaseName
    """
    # Build value restriction if allowed values are present
    value = None
    if prop_spec.enumeration:
        value = ifctester_ids.Restriction(
            options={"enumeration": prop_spec.enumeration},
            base="string",
        )

    # Build Property facet
    # Note: ifctester 0.8.x uses positional/keyword args:
    #   propertySet, baseName, value, dataType, uri, cardinality, instructions
    prop_facet = ifctester_ids.Property(
        propertySet=prop_spec.pset_name,
        baseName=prop_spec.base_name,
        value=value,
        dataType=prop_spec.data_type,
        uri=prop_spec.base_name_uri,
        cardinality=prop_spec.cardinality,
        instructions=prop_spec.instructions,
    )
    return prop_facet


def build_ids(
    spec_list: list[IDSSpecificationSpec],
    title: str,
    version: str = "0.1",
    description: str = "",
    author: str = "datadict@he-sem.ch",
    purpose: str = "",
) -> ifctester_ids.Ids:
    """
    Build a complete ifctester Ids object from a list of IDSSpecificationSpec.

    Args:
        spec_list:   One or more IDSSpecificationSpec (one per IDS <specification>).
        title:       IDS title (e.g. "KBOB Raum").
        version:     IDS version string.
        description: IDS-level description.
        author:      Email or name of the IDS author.
        purpose:     IDS purpose field (optional).

    Returns:
        ifctester.ids.Ids object ready for serialisation.
    """
    ids_doc = ifctester_ids.Ids(
        title=title,
        version=version,
        description=description or None,
        author=author or None,
        purpose=purpose or None,
    )

    for spec_spec in spec_list:
        specification = ifctester_ids.Specification(
            name=spec_spec.spec_name,
            ifcVersion=IFC_VERSION,
            description=spec_spec.description or None,
        )

        # ── Applicability: Entity ───────────────────────────────────────────
        entity_facet = ifctester_ids.Entity(
            name=spec_spec.ifc_entity,
            predefinedType=spec_spec.ifc_predefined_type,
        )
        specification.applicability.append(entity_facet)

        # ── Requirements: one Property facet per mapped property ─────────────
        for prop_spec in spec_spec.properties:
            prop_facet = _build_property_facet(prop_spec)
            specification.requirements.append(prop_facet)

        ids_doc.specifications.append(specification)

    return ids_doc
