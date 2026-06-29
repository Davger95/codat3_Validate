"""
SchemaForge — rdf_writer.py v2
Write RDF (TriG) from DataDictionary objects with all 6 improvements.
"""
from rdflib import Dataset, Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, OWL, SKOS, XSD, PROV
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from readers.excel_reader import load_dd, DataDictionary
from config import (
    GRAPH_KBOB, GRAPH_BDCH, GRAPH_MAPPINGS,
    KBOB_CLASS, KBOB_PROP, KBOB_PSET, KBOB_AVVALUE, KBOB_DICT_URI,
    BDCH_CLASS, BDCH_PROP, BDCH_PSET, BDCH_AVVALUE, BDCH_DICT_URI,
    HESEM_ONT,
    HESEM_C_DATADICT, HESEM_C_PSET, HESEM_C_ASSIGNMENT, HESEM_C_ALLOWEDVAL,
    HESEM_HAS_PROPERTY, HESEM_HAS_PSET, HESEM_CONTAINS_PROP, HESEM_PROPERTY_SET,
    HESEM_IFC_ENTITY, HESEM_IFC_PREDTYPE, HESEM_IFC_URI,
    HESEM_DATA_TYPE, HESEM_DATA_TYPE_IFC, HESEM_PROP_VAL_KIND, HESEM_PHYS_QTY,
    HESEM_MIN_VALUE, HESEM_MAX_VALUE, HESEM_UNIT_LABEL, HESEM_UNIT_QUDT,
    HESEM_PSET_NAME, HESEM_IFC_PROP_URI, HESEM_IFC_PSET_URI, HESEM_RDS_REF, HESEM_PROV,
    HESEM_HAS_AVAL, HESEM_VALUE_CODE, HESEM_SORT_NUMBER,
    HESEM_IS_REQUIRED, HESEM_IS_WRITABLE, HESEM_PREDEF_VAL, HESEM_UNIT_OVERRIDE,
    HESEM_LOIN_PHASE, HESEM_LOIN_ROLE, HESEM_LOIN_UC, HESEM_AVAL_OVERRIDE,
    HESEM_ORG_CODE, HESEM_VERSION, HESEM_STATUS, HESEM_COUNTRIES,
    BSDD, OUTPUT_DIR,
)

OUTPUT = OUTPUT_DIR / "dd_combined.trig"
PREFIXES = {
    "rdf": str(RDF), "rdfs": str(RDFS), "owl": str(OWL),
    "skos": str(SKOS), "xsd": str(XSD), "hesem": str(HESEM_ONT),
    "bsdd": str(BSDD), "kbob": "https://www.kbob.admin.ch/",
    "bdch": "https://bauen-digital.ch/", "prov": str(PROV),
}

def _uri(owned_uri, ns, code):
    return URIRef(owned_uri) if owned_uri else ns[code]

def _loose_typed(val):
    if val is None: return None
    s = str(val).strip()
    if not s: return None
    try:
        return Literal(float(s), datatype=XSD.double) if "." in s else Literal(int(s), datatype=XSD.integer)
    except: pass
    if s.lower() in ("true","false"): return Literal(s.lower()=="true", datatype=XSD.boolean)
    return Literal(s)

def _skos_relation(g, subj, rel_type, obj):
    rel_map = {"skos:exactMatch": SKOS.exactMatch, "skos:closeMatch": SKOS.closeMatch,
               "skos:broadMatch": SKOS.broadMatch, "skos:narrowMatch": SKOS.narrowMatch,
               "skos:relatedMatch": SKOS.relatedMatch}
    pred = rel_map.get(rel_type, SKOS.relatedMatch)
    if pred: g.add((subj, pred, obj))

# ── 6. Dictionary node ───────────────────────────────────────────────────────
def _emit_dictionary_node(g, dd, dict_uri):
    meta = dd.meta
    g.add((dict_uri, RDF.type, HESEM_C_DATADICT))
    g.add((dict_uri, RDF.type, SKOS.ConceptScheme))
    if meta.org_name_de: g.add((dict_uri, RDFS.label, Literal(meta.org_name_de, lang="de")))
    if meta.org_name_fr: g.add((dict_uri, RDFS.label, Literal(meta.org_name_fr, lang="fr")))
    if meta.org_name_en: g.add((dict_uri, RDFS.label, Literal(meta.org_name_en, lang="en")))
    if meta.org_code:    g.add((dict_uri, HESEM_ORG_CODE, Literal(meta.org_code)))
    if meta.dd_version:  g.add((dict_uri, HESEM_VERSION, Literal(meta.dd_version)))
    if meta.dd_status:   g.add((dict_uri, HESEM_STATUS, Literal(meta.dd_status)))
    if meta.countries:   g.add((dict_uri, HESEM_COUNTRIES, Literal(meta.countries)))
    if meta.dd_uri:      g.add((dict_uri, RDFS.seeAlso, URIRef(meta.dd_uri)))

# ── 1. PropertySets ──────────────────────────────────────────────────────────
def _ensure_propertyset(g, pset_name, dict_uri, ns_pset):
    if not pset_name: return None
    pset_uri = ns_pset[quote(pset_name, safe="")]
    if (pset_uri, RDF.type, None) not in g:
        g.add((pset_uri, RDF.type, HESEM_C_PSET))
        g.add((pset_uri, RDF.type, SKOS.Concept))
        g.add((pset_uri, RDFS.label, Literal(pset_name)))
        g.add((pset_uri, SKOS.inScheme, dict_uri))
    return pset_uri

# ── 2. Class hierarchy ───────────────────────────────────────────────────────
def _add_class_hierarchy(g, cls_uri, parent_uri):
    if parent_uri and parent_uri != cls_uri:
        g.add((cls_uri, SKOS.broader, parent_uri))
        g.add((parent_uri, SKOS.narrower, cls_uri))
        g.add((cls_uri, RDFS.subClassOf, parent_uri))

# ── 3. Full property semantics ───────────────────────────────────────────────
def _add_property_semantics(g, p, prop_uri):
    if p.data_type:                      g.add((prop_uri, HESEM_DATA_TYPE, Literal(p.data_type)))
    if p.data_type_ifc:                  g.add((prop_uri, HESEM_DATA_TYPE_IFC, Literal(p.data_type_ifc)))
    if getattr(p,'property_value_kind',None): g.add((prop_uri, HESEM_PROP_VAL_KIND, Literal(p.property_value_kind)))
    if getattr(p,'physical_quantity',None):   g.add((prop_uri, HESEM_PHYS_QTY, Literal(p.physical_quantity)))
    if getattr(p,'min_value',None) is not None:
        lit = _loose_typed(p.min_value)
        if lit: g.add((prop_uri, HESEM_MIN_VALUE, lit))
    if getattr(p,'max_value',None) is not None:
        lit = _loose_typed(p.max_value)
        if lit: g.add((prop_uri, HESEM_MAX_VALUE, lit))
    if getattr(p,'unit_label',None):     g.add((prop_uri, HESEM_UNIT_LABEL, Literal(p.unit_label)))
    if getattr(p,'unit_qudt_iri',None):  g.add((prop_uri, HESEM_UNIT_QUDT, URIRef(p.unit_qudt_iri)))
    if getattr(p,'ifc_property_uri',None):
        g.add((prop_uri, HESEM_IFC_PROP_URI, URIRef(p.ifc_property_uri)))
        g.add((prop_uri, SKOS.exactMatch, URIRef(p.ifc_property_uri)))
    if getattr(p,'ifc_pset_uri',None):   g.add((prop_uri, HESEM_IFC_PSET_URI, URIRef(p.ifc_pset_uri)))
    if getattr(p,'rds_reference',None):  g.add((prop_uri, HESEM_RDS_REF, Literal(p.rds_reference)))
    if getattr(p,'prov_attributed_to',None): g.add((prop_uri, PROV.wasAttributedTo, Literal(p.prov_attributed_to)))

# ── 4. AllowedValues ─────────────────────────────────────────────────────────
def _emit_allowed_values(g, dd, dict_uri, ns_av):
    by_prop = {}
    for av in dd.allowed_values:
        by_prop.setdefault(av.property_code, []).append(av)
    for prop_code, avs in by_prop.items():
        p_obj = dd.property_index.get(prop_code)
        prop_uri = _uri(p_obj.owned_uri if p_obj else None, dd._prop_ns, prop_code)
        for av in avs:
            av_uri = ns_av[f"{prop_code}/{av.code}"]
            g.add((av_uri, RDF.type, HESEM_C_ALLOWEDVAL))
            g.add((av_uri, RDF.type, SKOS.Concept))
            g.add((av_uri, SKOS.inScheme, dict_uri))
            g.add((av_uri, HESEM_VALUE_CODE, Literal(av.code)))
            if av.value_de: g.add((av_uri, SKOS.prefLabel, Literal(av.value_de, lang="de")))
            if av.value_fr: g.add((av_uri, SKOS.prefLabel, Literal(av.value_fr, lang="fr")))
            if av.value_en: g.add((av_uri, SKOS.prefLabel, Literal(av.value_en, lang="en")))
            if getattr(av,'definition_de',None): g.add((av_uri, SKOS.definition, Literal(av.definition_de, lang="de")))
            if getattr(av,'sort_number',None) is not None: g.add((av_uri, HESEM_SORT_NUMBER, Literal(av.sort_number, datatype=XSD.integer)))
            if getattr(av,'skos_exact_match',None): g.add((av_uri, SKOS.exactMatch, URIRef(av.skos_exact_match)))
            if prop_uri: g.add((prop_uri, HESEM_HAS_AVAL, av_uri))

# ── Main graph builder ───────────────────────────────────────────────────────
def dd_to_graph(dd, ns_class, ns_prop, ns_pset, ns_av, dict_uri, dict_code):
    g = Graph()
    for prefix, uri in PREFIXES.items():
        g.bind(prefix, uri)
    _emit_dictionary_node(g, dd, dict_uri)
    class_index = {c.code: c for c in dd.classes}
    prop_index  = {p.code: p for p in dd.properties}
    # class_index already available as local var
    # prop_index already available as local var
    object.__setattr__(dd, "_prop_ns", ns_prop)
    object.__setattr__(dd, "_av_ns", ns_av)
    if dd.allowed_values:
        _emit_allowed_values(g, dd, dict_uri, ns_av)
    # Classes
    for c in dd.classes:
        cls_uri = _uri(c.owned_uri, ns_class, c.code)
        g.add((cls_uri, RDF.type, SKOS.Concept))
        g.add((cls_uri, RDF.type, OWL.NamedIndividual))
        g.add((cls_uri, SKOS.inScheme, dict_uri))
        if c.name_de: g.add((cls_uri, RDFS.label, Literal(c.name_de, lang="de")))
        if c.name_fr: g.add((cls_uri, RDFS.label, Literal(c.name_fr, lang="fr")))
        if c.name_en: g.add((cls_uri, RDFS.label, Literal(c.name_en, lang="en")))
        if c.definition_de: g.add((cls_uri, SKOS.definition, Literal(c.definition_de, lang="de")))
        if c.definition_fr: g.add((cls_uri, SKOS.definition, Literal(c.definition_fr, lang="fr")))
        if getattr(c,'parent_class_code',None):
            parent_obj = class_index.get(c.parent_class_code)
            if parent_obj:
                parent_uri = _uri(parent_obj.owned_uri, ns_class, parent_obj.code)
                _add_class_hierarchy(g, cls_uri, parent_uri)
        if getattr(c,'ifc_entity_code',None):    g.add((cls_uri, HESEM_IFC_ENTITY, Literal(c.ifc_entity_code)))
        if getattr(c,'ifc_predefined_type',None): g.add((cls_uri, HESEM_IFC_PREDTYPE, Literal(c.ifc_predefined_type)))
        if getattr(c,'ifc_uri',None):
            g.add((cls_uri, HESEM_IFC_URI, URIRef(c.ifc_uri)))
            g.add((cls_uri, SKOS.closeMatch, URIRef(c.ifc_uri)))
        if getattr(c,'status',None): g.add((cls_uri, SKOS.note, Literal(f"status:{c.status}")))
    # Properties
    for p in dd.properties:
        prop_uri = _uri(p.owned_uri, ns_prop, p.code)
        g.add((prop_uri, RDF.type, SKOS.Concept))
        g.add((prop_uri, RDF.type, OWL.NamedIndividual))
        g.add((prop_uri, SKOS.inScheme, dict_uri))
        if p.name_de: g.add((prop_uri, RDFS.label, Literal(p.name_de, lang="de")))
        if p.name_fr: g.add((prop_uri, RDFS.label, Literal(p.name_fr, lang="fr")))
        if p.name_en: g.add((prop_uri, RDFS.label, Literal(p.name_en, lang="en")))
        if p.definition_de: g.add((prop_uri, SKOS.definition, Literal(p.definition_de, lang="de")))
        if p.definition_fr: g.add((prop_uri, SKOS.definition, Literal(p.definition_fr, lang="fr")))
        _add_property_semantics(g, p, prop_uri)
        if getattr(p,'property_set_name',None):
            pset_uri = _ensure_propertyset(g, p.property_set_name, dict_uri, ns_pset)
            if pset_uri: g.add((pset_uri, HESEM_CONTAINS_PROP, prop_uri))
    # ClassProperty assignments (improvements 1 & 5)
    ASGN_CLASS = HESEM_ONT.assignedClass
    ASGN_PROP  = HESEM_ONT.assignedProperty
    for cp in dd.class_properties:
        c_obj = class_index.get(cp.class_code)
        p_obj = prop_index.get(cp.property_code)
        if not c_obj or not p_obj: continue
        cls_uri  = _uri(c_obj.owned_uri, ns_class, c_obj.code)
        prop_uri = _uri(p_obj.owned_uri, ns_prop,  p_obj.code)
        pset_name = cp.property_set_name or p_obj.property_set_name
        pset_uri  = _ensure_propertyset(g, pset_name, dict_uri, ns_pset) if pset_name else None
        g.add((cls_uri, HESEM_HAS_PROPERTY, prop_uri))
        asgn_uri = HESEM_ONT[f"Assignment_{cp.class_code}_{cp.property_code}"]
        g.add((asgn_uri, RDF.type,    HESEM_C_ASSIGNMENT))
        g.add((asgn_uri, ASGN_CLASS,  cls_uri))
        g.add((asgn_uri, ASGN_PROP,   prop_uri))
        g.add((asgn_uri, HESEM_IS_REQUIRED, Literal(cp.is_required, datatype=XSD.boolean)))
        g.add((asgn_uri, HESEM_IS_WRITABLE, Literal(cp.is_writable, datatype=XSD.boolean)))
        if pset_uri:
            g.add((asgn_uri, HESEM_PROPERTY_SET, pset_uri))
            g.add((asgn_uri, HESEM_PSET_NAME, Literal(pset_name)))
            g.add((cls_uri,  HESEM_HAS_PSET,  pset_uri))
            g.add((pset_uri, HESEM_CONTAINS_PROP, prop_uri))
        if getattr(cp,'sort_number',None) is not None:
            g.add((asgn_uri, HESEM_SORT_NUMBER, Literal(cp.sort_number, datatype=XSD.integer)))
        if getattr(cp,'predefined_value',None):  g.add((asgn_uri, HESEM_PREDEF_VAL,    Literal(cp.predefined_value)))
        if getattr(cp,'unit_override',None):      g.add((asgn_uri, HESEM_UNIT_OVERRIDE, Literal(cp.unit_override)))
        if getattr(cp,'loin_sia_phase',None):     g.add((asgn_uri, HESEM_LOIN_PHASE,    Literal(cp.loin_sia_phase)))
        if getattr(cp,'loin_role',None):          g.add((asgn_uri, HESEM_LOIN_ROLE,     Literal(cp.loin_role)))
        if getattr(cp,'loin_use_case',None):      g.add((asgn_uri, HESEM_LOIN_UC,       Literal(cp.loin_use_case)))
        if getattr(cp,'allowed_values_override',None): g.add((asgn_uri, HESEM_AVAL_OVERRIDE, Literal(cp.allowed_values_override)))
    return g

# ── Mappings graph ────────────────────────────────────────────────────────────
def build_mappings_graph(dds):
    g = Graph()
    for prefix, uri in PREFIXES.items():
        g.bind(prefix, uri)
    for dd, ns_class, ns_prop in dds:
        for cr in dd.concept_relations:
            subj = None
            c_obj = dd.class_index.get(cr.subject_code)
            p_obj = dd.property_index.get(cr.subject_code)
            if c_obj:   subj = _uri(c_obj.owned_uri, ns_class, c_obj.code)
            elif p_obj: subj = _uri(p_obj.owned_uri, ns_prop,  p_obj.code)
            else:       subj = ns_prop[cr.subject_code]
            obj = URIRef(cr.related_uri)
            _skos_relation(g, subj, cr.relation_type, obj)
            if cr.notes: g.add((subj, RDFS.comment, Literal(cr.notes)))
    return g

# ── Main writer ───────────────────────────────────────────────────────────────
def write_trig(kbob_dd, bdch_dd, outpath=None):
    if outpath is None:
        outpath = OUTPUT
    ds = Dataset()
    for prefix, uri in PREFIXES.items():
        ds.bind(prefix, uri)
    g_kbob = ds.graph(GRAPH_KBOB)
    g_bdch = ds.graph(GRAPH_BDCH)
    g_map  = ds.graph(GRAPH_MAPPINGS)
    kbob_content = dd_to_graph(kbob_dd, KBOB_CLASS, KBOB_PROP, KBOB_PSET, KBOB_AVVALUE, KBOB_DICT_URI, "kbob")
    bdch_content = dd_to_graph(bdch_dd, BDCH_CLASS, BDCH_PROP, BDCH_PSET, BDCH_AVVALUE, BDCH_DICT_URI, "bdch")
    map_content  = build_mappings_graph([
        (kbob_dd, KBOB_CLASS, KBOB_PROP),
        (bdch_dd, BDCH_CLASS, BDCH_PROP),
    ])
    for s, p, o in kbob_content: g_kbob.add((s, p, o))
    for s, p, o in bdch_content: g_bdch.add((s, p, o))
    for s, p, o in map_content:  g_map.add((s, p, o))
    outpath = Path(outpath)
    ds.serialize(destination=str(outpath), format="trig")
    return outpath

# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    base = Path(__file__).resolve().parents[3] / "HE_SEM_shemaforge"
    print(f"Loading KBOB DD from {base / 'DD_KBOB_v0.4.xlsx'}")
    kbob = load_dd(base / "DD_KBOB_v0.4.xlsx")
    print(f"Loading bDCH DD from {base / 'DD_bDCH_v0.4.xlsx'}")
    bdch = load_dd(base / "DD_bDCH_v0.4.xlsx")
    out = write_trig(kbob, bdch)
    print(f"Wrote: {out}  ({out.stat().st_size:,} bytes)")
