"""
SchemaForge IDS Pipeline — graph_retriever.py
=============================================
Retrieves semantic structures from GraphDB via SPARQL.
All queries are parameterised; no Excel parsing.

Architecture:
    GraphDB SPARQL → graph_retriever → ids_mapper → ids_builder → ids_writer
"""

import json
import subprocess
from dataclasses import dataclass, field
from typing import Optional

# ── GraphDB connection config ─────────────────────────────────────────────────
GRAPHDB_SSH_HOST    = "davger95@KPF5AA5S0"
GRAPHDB_SSH_KEY     = "/home/Dave/.ssh/schemaforge_deploy_ed25519"
GRAPHDB_SPARQL_URL  = "http://localhost:7200/repositories/PoC_Repo"

# ── Named graph IRIs ───────────────────────────────────────────────────────────
GRAPH_KBOB     = "https://www.kbob.admin.ch/graph/dd"
GRAPH_BDCH     = "https://bauen-digital.ch/graph/dd"
GRAPH_MAPPINGS = "https://he-sem.ch/graph/mappings"


# ── Data containers ────────────────────────────────────────────────────────────

@dataclass
class AllowedValueInfo:
    code: str
    label: Optional[str] = None


@dataclass
class PropertyInfo:
    uri: str
    label: str
    data_type: str                         # HE-SEM type: STRING / BOOLEAN / REAL …
    pset_name: Optional[str] = None        # IDS PropertySet name (literal)
    pset_uri: Optional[str] = None         # PropertySet URI
    ifc_prop_uri: Optional[str] = None     # bSDD property IRI
    ifc_pset_uri: Optional[str] = None     # bSDD Pset IRI
    is_required: bool = True
    allowed_values: list[AllowedValueInfo] = field(default_factory=list)
    assign_uri: Optional[str] = None       # originating Assignment IRI (traceability)


@dataclass
class ClassInfo:
    uri: str
    label: str
    ifc_entity: str                        # e.g. "IfcSpace"
    ifc_predefined_type: Optional[str]     # e.g. "GFA" or None
    ifc_class_uri: Optional[str]           # bSDD class IRI


@dataclass
class DictionarySpec:
    """Complete semantic payload for one dictionary class, ready for IDS mapping."""
    kbob_class: ClassInfo
    bdch_class: Optional[ClassInfo]
    properties: list[PropertyInfo] = field(default_factory=list)


# ── SPARQL helpers ─────────────────────────────────────────────────────────────

def _sparql(query: str) -> list[dict]:
    """Run a SPARQL SELECT against GraphDB via SSH, return list of binding dicts."""
    cmd = [
        "ssh",
        "-i", GRAPHDB_SSH_KEY,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        GRAPHDB_SSH_HOST,
        f"curl -s -G '{GRAPHDB_SPARQL_URL}' "
        f"--data-urlencode 'query={query}' "
        f"-H 'Accept: application/sparql-results+json'",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"SSH/SPARQL error: {result.stderr}")
    data = json.loads(result.stdout)
    return data["results"]["bindings"]


def _val(binding: dict, key: str) -> Optional[str]:
    """Safely extract a SPARQL binding value."""
    entry = binding.get(key)
    return entry["value"] if entry else None


# ── Retrieval functions ────────────────────────────────────────────────────────

def get_class_info(class_uri: str, graph: str) -> ClassInfo:
    """Retrieve class metadata (IFC entity, predefined type, label) from a named graph."""
    q = f"""
PREFIX hesem: <https://he-sem.ch/ontology/>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?label ?ifcEntity ?ifcPredef ?ifcClassUri WHERE {{
  GRAPH <{graph}> {{
    <{class_uri}> rdfs:label ?label .
    OPTIONAL {{ <{class_uri}> hesem:ifcEntityCode  ?ifcEntity }}
    OPTIONAL {{ <{class_uri}> hesem:ifcPredefinedType ?ifcPredef }}
    OPTIONAL {{ <{class_uri}> hesem:ifcClassUri    ?ifcClassUri }}
    FILTER(LANG(?label) = "de" || LANG(?label) = "" || LANG(?label) = "en")
  }}
}}
LIMIT 1
"""
    rows = _sparql(q)
    if not rows:
        raise ValueError(f"Class not found in graph: {class_uri} / {graph}")
    r = rows[0]
    return ClassInfo(
        uri=class_uri,
        label=_val(r, "label") or class_uri.split("/")[-1],
        ifc_entity=_val(r, "ifcEntity") or "IfcProduct",
        ifc_predefined_type=_val(r, "ifcPredef"),
        ifc_class_uri=_val(r, "ifcClassUri"),
    )


def get_assignments_for_class(class_uri: str, graph: str) -> list[PropertyInfo]:
    """
    Retrieve all property assignments for a class URI from a named graph.
    Groups allowed values per property, respects isRequired.
    Returns deduplicated PropertyInfo list.
    """
    q = f"""
PREFIX hesem: <https://he-sem.ch/ontology/>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?assign ?prop ?propLabel ?psetName ?psetUri
       ?required ?dataType ?avCode ?avLabel
       ?ifcPropUri ?ifcPsetUri
WHERE {{
  GRAPH <{graph}> {{
    ?assign a hesem:Assignment ;
            hesem:assignedClass  <{class_uri}> ;
            hesem:assignedProperty ?prop .
    ?prop rdfs:label ?propLabel .
    OPTIONAL {{ ?assign hesem:propertySetName  ?psetName  }}
    OPTIONAL {{ ?assign hesem:propertySet      ?psetUri   }}
    OPTIONAL {{ ?assign hesem:isRequired       ?required  }}
    OPTIONAL {{ ?prop   hesem:dataType         ?dataType  }}
    OPTIONAL {{ ?prop   hesem:ifcPropertyUri   ?ifcPropUri }}
    OPTIONAL {{ ?prop   hesem:ifcPsetUri       ?ifcPsetUri }}
    OPTIONAL {{
      ?prop hesem:hasAllowedValue ?av .
      ?av   hesem:valueCode ?avCode .
      OPTIONAL {{ ?av rdfs:label ?avLabel }}
    }}
  }}
}}
ORDER BY ?assign ?avCode
"""
    rows = _sparql(q)

    # Group rows by property URI, collect allowed values
    props: dict[str, PropertyInfo] = {}
    for r in rows:
        prop_uri = _val(r, "prop")
        if prop_uri not in props:
            props[prop_uri] = PropertyInfo(
                uri=prop_uri,
                label=_val(r, "propLabel") or prop_uri.split("/")[-1],
                data_type=_val(r, "dataType") or "STRING",
                pset_name=_val(r, "psetName"),
                pset_uri=_val(r, "psetUri"),
                ifc_prop_uri=_val(r, "ifcPropUri"),
                ifc_pset_uri=_val(r, "ifcPsetUri"),
                is_required=(_val(r, "required") == "true"),
                assign_uri=_val(r, "assign"),
            )
        av_code = _val(r, "avCode")
        if av_code:
            # Deduplicate allowed values
            existing = {av.code for av in props[prop_uri].allowed_values}
            if av_code not in existing:
                props[prop_uri].allowed_values.append(
                    AllowedValueInfo(code=av_code, label=_val(r, "avLabel"))
                )

    return list(props.values())


def get_mapped_bdch_class(kbob_class_uri: str) -> Optional[str]:
    """
    Follow SKOS mappings from a KBOB class to a bDCH class.
    Uses skos:closeMatch / skos:exactMatch / skos:broadMatch in mappings graph or KBOB graph.
    Returns the first bDCH class URI found, or None.
    """
    q = f"""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?bdchClass WHERE {{
  {{
    GRAPH <{GRAPH_KBOB}> {{
      <{kbob_class_uri}> skos:closeMatch|skos:exactMatch|skos:broadMatch|skos:relatedMatch ?bdchClass .
      FILTER(STRSTARTS(str(?bdchClass), "https://bauen-digital.ch/"))
    }}
  }} UNION {{
    GRAPH <{GRAPH_MAPPINGS}> {{
      <{kbob_class_uri}> skos:closeMatch|skos:exactMatch|skos:broadMatch|skos:relatedMatch ?bdchClass .
      FILTER(STRSTARTS(str(?bdchClass), "https://bauen-digital.ch/"))
    }}
  }}
}}
LIMIT 1
"""
    rows = _sparql(q)
    if rows:
        return _val(rows[0], "bdchClass")
    return None


def get_dictionary_spec(
    kbob_class_uri: str,
    target_property_uris: Optional[list[str]] = None,
) -> DictionarySpec:
    """
    Assemble a complete DictionarySpec for a KBOB class:
    - Retrieves KBOB class metadata
    - Finds mapped bDCH class via SKOS
    - Retrieves all bDCH assignments (or filtered subset if target_property_uris given)
    - Returns DictionarySpec ready for IDS mapping

    Args:
        kbob_class_uri: IRI of the KBOB class, e.g. "https://www.kbob.admin.ch/class/raum"
        target_property_uris: Optional list of property URIs to restrict retrieval to.
    """
    kbob_class = get_class_info(kbob_class_uri, GRAPH_KBOB)

    bdch_class_uri = get_mapped_bdch_class(kbob_class_uri)
    bdch_class = None
    properties = []

    if bdch_class_uri:
        bdch_class = get_class_info(bdch_class_uri, GRAPH_BDCH)
        properties = get_assignments_for_class(bdch_class_uri, GRAPH_BDCH)

        # Filter to target properties if requested
        if target_property_uris:
            target_set = set(target_property_uris)
            properties = [p for p in properties if p.uri in target_set]

    return DictionarySpec(
        kbob_class=kbob_class,
        bdch_class=bdch_class,
        properties=properties,
    )
