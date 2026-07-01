"""
SchemaForge — config.py
Namespace declarations, graph IRIs, file paths.
All namespace IRIs must end with # or / so rdflib prefix binding works correctly.
"""

from rdflib import Namespace, URIRef
from pathlib import Path

# ── Base paths ────────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).resolve().parents[2]
SHEMAFORGE_DIR = WORKSPACE / "HE_SEM_shemaforge"
OUTPUT_DIR = WORKSPACE / "Validation_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Input files ───────────────────────────────────────────────────────────────
DD_KBOB = SHEMAFORGE_DIR / "DD_KBOB_v0.4.xlsx"
DD_BDCH = SHEMAFORGE_DIR / "DD_bDCH_v0.4.xlsx"

# ── RDF Namespaces ────────────────────────────────────────────────────────────

# ifcOWL — the namespace produced by the UGent IFCtoRDF converter (IFC4x3 ADD2)
IFCOWL = Namespace("http://standards.buildingsmart.org/IFC/DEV/IFC4x3/ADD2/OWL#")

# bSDD identifier namespace
BSDD = Namespace("https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/")
BSDD_DEF = Namespace("https://identifier.buildingsmart.org/def/bsdd/")

# Standard vocabularies
from rdflib.namespace import RDF, RDFS, OWL, SKOS, XSD, DCTERMS
QUDT_UNIT = Namespace("http://qudt.org/vocab/unit/")
QUDT_SCHEMA = Namespace("http://qudt.org/schema/qudt/")
PROV = Namespace("http://www.w3.org/ns/prov#")
SHACL = Namespace("http://www.w3.org/ns/shacl#")
EXPRESS = Namespace("https://w3id.org/express#")

# Dictionary-specific namespaces (match OwnedUri patterns in the Excel files)
KBOB_NS       = Namespace("https://www.kbob.admin.ch/")
KBOB_CLASS    = Namespace("https://www.kbob.admin.ch/class/")
KBOB_PROP     = Namespace("https://www.kbob.admin.ch/property/")
KBOB_VALUE    = Namespace("https://www.kbob.admin.ch/value/")
KBOB_PSET     = Namespace("https://www.kbob.admin.ch/propertyset/")
KBOB_AVVALUE  = Namespace("https://www.kbob.admin.ch/property/")   # value IRIs: /property/{pcode}/value/{vcode}
KBOB_DICT_URI = URIRef("https://www.kbob.admin.ch/dictionary/kbob")

BDCH_NS       = Namespace("https://bauen-digital.ch/")
BDCH_CLASS    = Namespace("https://bauen-digital.ch/class/")
BDCH_PROP     = Namespace("https://bauen-digital.ch/property/")
BDCH_VALUE    = Namespace("https://bauen-digital.ch/value/")
BDCH_PSET     = Namespace("https://bauen-digital.ch/propertyset/")
BDCH_AVVALUE  = Namespace("https://bauen-digital.ch/property/")    # value IRIs: /property/{pcode}/value/{vcode}
BDCH_DICT_URI = URIRef("https://bauen-digital.ch/dictionary/bdch")

INTOP         = Namespace("https://lindas.admin.ch/ontology/intop/")

# Named graphs
GRAPH_KBOB       = URIRef("https://www.kbob.admin.ch/graph/dd")
GRAPH_BDCH       = URIRef("https://bauen-digital.ch/graph/dd")
GRAPH_MAPPINGS   = URIRef("https://lindas.admin.ch/graph/mappings")
GRAPH_SHACL_KBOB = URIRef("https://www.kbob.admin.ch/graph/shacl")
GRAPH_SHACL_BDCH = URIRef("https://bauen-digital.ch/graph/shacl")

# ── INTOP ontology predicates ───────────────────────────────────────────────
INTOP_ONT = Namespace("https://lindas.admin.ch/ontology/intop/")

# --- Classes (rdf:type targets) ---
INTOP_C_DATADICT   = INTOP_ONT.DataDictionary     # dictionary resource
INTOP_C_PSET       = INTOP_ONT.PropertySet        # property set resource
INTOP_C_ASSIGNMENT = INTOP_ONT.Assignment         # class-property assignment
INTOP_C_ALLOWEDVAL = INTOP_ONT.AllowedValue       # enumeration value

# --- Class-level predicates ---
INTOP_IFC_ENTITY   = INTOP_ONT.ifcEntityCode        # string e.g. "IfcBuilding"
INTOP_IFC_PREDTYPE = INTOP_ONT.ifcPredefinedType    # string e.g. "GFA"
INTOP_IFC_URI      = INTOP_ONT.ifcClassUri          # bSDD class IRI
INTOP_HAS_PROPERTY = INTOP_ONT.hasProperty          # class → property
INTOP_HAS_PSET     = INTOP_ONT.hasPropertySet       # class → PropertySet

# --- PropertySet predicates ---
INTOP_CONTAINS_PROP = INTOP_ONT.containsProperty    # PropertySet → property
INTOP_PROPERTY_SET  = INTOP_ONT.propertySet         # Assignment → PropertySet (URI link)

# --- Property-level predicates ---
INTOP_DATA_TYPE      = INTOP_ONT.dataType            # local DD type: STRING/REAL/BOOLEAN…
INTOP_DATA_TYPE_IFC  = INTOP_ONT.dataTypeIfc         # IFC schema type e.g. IfcLabel
INTOP_PROP_VAL_KIND  = INTOP_ONT.propertyValueKind   # Single / List / Bounded
INTOP_PHYS_QTY       = INTOP_ONT.physicalQuantity    # free-text physical quantity
INTOP_MIN_VALUE      = INTOP_ONT.minValue            # typed literal
INTOP_MAX_VALUE      = INTOP_ONT.maxValue            # typed literal
INTOP_UNIT_LABEL     = INTOP_ONT.unitLabel           # human-readable unit string
INTOP_UNIT_QUDT      = INTOP_ONT.unitQudtIri         # QUDT unit IRI
INTOP_PSET_NAME      = INTOP_ONT.propertySetName     # literal (IDS compatibility)
INTOP_IFC_PROP_URI   = INTOP_ONT.ifcPropertyUri      # bSDD property IRI
INTOP_IFC_PSET_URI   = INTOP_ONT.ifcPsetUri          # bSDD Pset IRI
INTOP_RDS_REF        = INTOP_ONT.rdsReference        # RDS/CCS reference string
INTOP_PROV           = INTOP_ONT.attributedTo        # provenance string
INTOP_HAS_AVAL       = INTOP_ONT.hasAllowedValue     # property → AllowedValue

# --- AllowedValue predicates ---
INTOP_VALUE_CODE   = INTOP_ONT.valueCode             # string code
INTOP_SORT_NUMBER  = INTOP_ONT.sortNumber            # xsd:integer (shared with CP)

# --- ClassProperty / Assignment predicates ---
INTOP_IS_REQUIRED  = INTOP_ONT.isRequired            # xsd:boolean
INTOP_IS_WRITABLE  = INTOP_ONT.isWritable            # xsd:boolean
INTOP_PREDEF_VAL   = INTOP_ONT.predefinedValue       # string override
INTOP_UNIT_OVERRIDE= INTOP_ONT.unitOverride          # unit string override
INTOP_LOIN_PHASE   = INTOP_ONT.loinSiaPhase          # string
INTOP_LOIN_ROLE    = INTOP_ONT.loinRole              # string
INTOP_LOIN_UC      = INTOP_ONT.loinUseCase           # string
INTOP_AVAL_OVERRIDE= INTOP_ONT.allowedValuesOverride # string

# --- Dictionary-level predicates ---
INTOP_ORG_CODE     = INTOP_ONT.organizationCode      # string
INTOP_VERSION      = INTOP_ONT.version               # string
INTOP_STATUS       = INTOP_ONT.status                # string
INTOP_COUNTRIES    = INTOP_ONT.countriesOfUse        # string

# ── DataType mapping: HE-SEM → XSD ───────────────────────────────────────────
DATATYPE_MAP = {
    "BOOLEAN":  XSD.boolean,
    "INTEGER":  XSD.integer,
    "REAL":     XSD.double,
    "STRING":   XSD.string,
    "TIME":     XSD.date,
    "DATETIME": XSD.dateTime,
}

# ── ifcOWL express value properties per datatype ─────────────────────────────
EXPRESS_LITERAL_PROP = {
    XSD.string:   EXPRESS.hasString,
    XSD.boolean:  EXPRESS.hasBoolean,
    XSD.integer:  EXPRESS.hasInteger,
    XSD.double:   EXPRESS.hasDouble,
    XSD.date:     EXPRESS.hasString,
    XSD.dateTime: EXPRESS.hasString,
}
