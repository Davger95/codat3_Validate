from rdflib import Dataset, Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, OWL, SKOS, XSD, PROV, DCTERMS
from pathlib import Path
from urllib.parse import quote
from readers.excel_reader import load_dd
from config import INTOP_ONT, OUTPUT_DIR, IFCOWL

OUTPUT = OUTPUT_DIR / 'dd_combined.trig'
PREFIXES = {
    'rdf': str(RDF), 'rdfs': str(RDFS), 'owl': str(OWL), 'skos': str(SKOS),
    'xsd': str(XSD), 'prov': str(PROV), 'dct': str(DCTERMS), 'intop': str(INTOP_ONT), 'ifc': str(IFCOWL),
}

REL_MAP = {
    'skos:exactMatch': SKOS.exactMatch,
    'skos:closeMatch': SKOS.closeMatch,
    'skos:broadMatch': SKOS.broadMatch,
    'skos:narrowMatch': SKOS.narrowMatch,
    'skos:relatedMatch': SKOS.relatedMatch,
    'owl:sameAs': OWL.sameAs,
}


def _dd_segments(dd):
    org1 = (dd.meta.raw.get('OrganizationCodeLindas') or 'FOBL').upper()
    org2 = (dd.meta.raw.get('OrganizationCode') or dd.meta.org_code or org1).upper()
    dd_code = (dd.meta.raw.get('DictionaryCode') or 'DD').strip()
    dd_code = dd_code.upper().replace(' ', '_').replace('-', '_')
    return org1, org2, dd_code


def _ns_for_dd(dd):
    org1, org2, dd_code = _dd_segments(dd)
    base = f'https://lindas.admin.ch/{org1}/{org2}/{dd_code}/'
    graph_uri = f'{base}graph/dd'
    return {
        'base': base,
        'class': Namespace(f'{base}class/'),
        'property': Namespace(f'{base}property/'),
        'allowed': Namespace(f'{base}allowed-value/'),
        'pset': Namespace(f'{base}property-set/'),
        'document': Namespace(f'{base}document/'),
        'document-group': Namespace(f'{base}document-group/'),
        'dict': URIRef(dd.meta.dd_uri or f'{base}dictionary'),
        'graph': URIRef(graph_uri)
    }


def _uri(owned_uri, ns, code):
    return URIRef(owned_uri) if owned_uri else ns[quote(str(code), safe='')]


def _add_labels_defs(g, uri, name_de=None, name_fr=None, name_en=None, def_de=None, def_fr=None):
    if name_de: g.add((uri, RDFS.label, Literal(name_de, lang='de')))
    if name_fr: g.add((uri, RDFS.label, Literal(name_fr, lang='fr')))
    if name_en: g.add((uri, RDFS.label, Literal(name_en, lang='en')))
    if def_de: g.add((uri, SKOS.definition, Literal(def_de, lang='de')))
    if def_fr: g.add((uri, SKOS.definition, Literal(def_fr, lang='fr')))


def dd_to_graph(dd):
    ns = _ns_for_dd(dd)
    g = Graph(identifier=ns['graph'])
    for prefix, uri in PREFIXES.items():
        g.bind(prefix, uri)

    dict_uri = ns['dict']
    g.add((dict_uri, RDF.type, SKOS.ConceptScheme))
    g.add((dict_uri, RDF.type, INTOP_ONT.DataDictionary))
    if dd.meta.org_code:
        g.add((dict_uri, INTOP_ONT.organizationCode, Literal(dd.meta.org_code)))
    if dd.meta.raw.get('DictionaryCode'):
        g.add((dict_uri, INTOP_ONT.dictionaryCode, Literal(dd.meta.raw.get('DictionaryCode'))))
    if dd.meta.dd_version:
        g.add((dict_uri, INTOP_ONT.version, Literal(dd.meta.dd_version)))
    if dd.meta.dd_status:
        g.add((dict_uri, INTOP_ONT.status, Literal(dd.meta.dd_status)))

    class_index = {}
    prop_index = {}
    for c in dd.classes:
        cu = _uri(c.owned_uri, ns['class'], c.code)
        class_index[c.code] = cu
        g.add((cu, RDF.type, SKOS.Concept))
        g.add((cu, SKOS.inScheme, dict_uri))
        _add_labels_defs(g, cu, c.name_de, c.name_fr, c.name_en, c.definition_de, c.definition_fr)
        if c.parent_class_code and c.parent_class_code in class_index:
            g.add((cu, SKOS.broader, class_index[c.parent_class_code]))
        if getattr(c, 'ifc_entity_code', None):
            g.add((cu, INTOP_ONT.ifcEntityCode, Literal(c.ifc_entity_code)))
        if getattr(c, 'ifc_predefined_type', None):
            g.add((cu, INTOP_ONT.ifcPredefinedType, Literal(c.ifc_predefined_type)))
        if getattr(c, 'ifc_type_object_entity_code', None):
            g.add((cu, INTOP_ONT.ifcTypeObjectEntityCode, Literal(getattr(c, 'ifc_type_object_entity_code'))))
        if c.ifc_uri:
            g.add((cu, SKOS.closeMatch, URIRef(c.ifc_uri)))

    for p in dd.properties:
        pu = _uri(p.owned_uri, ns['property'], p.code)
        prop_index[p.code] = pu
        g.add((pu, RDF.type, SKOS.Concept))
        g.add((pu, SKOS.inScheme, dict_uri))
        _add_labels_defs(g, pu, p.name_de, p.name_fr, p.name_en, p.definition_de, p.definition_fr)
        if p.data_type: g.add((pu, INTOP_ONT.dataType, Literal(p.data_type)))
        if p.data_type_ifc: g.add((pu, INTOP_ONT.dataTypeIfc, Literal(p.data_type_ifc)))
        if p.property_set_name:
            psu = ns['pset'][quote(str(p.property_set_name), safe='')]
            g.add((psu, RDF.type, INTOP_ONT.PropertySet))
            g.add((psu, SKOS.inScheme, dict_uri))
            g.add((psu, RDFS.label, Literal(p.property_set_name)))
            g.add((psu, INTOP_ONT.containsProperty, pu))
            g.add((pu, INTOP_ONT.propertySet, psu))
        if p.ifc_property_uri:
            g.add((pu, SKOS.exactMatch, URIRef(p.ifc_property_uri)))

    for av in dd.allowed_values:
        au = _uri(av.owned_uri, ns['allowed'], f'{av.property_code}/{av.code}')
        g.add((au, RDF.type, INTOP_ONT.AllowedValue))
        g.add((au, SKOS.inScheme, dict_uri))
        _add_labels_defs(g, au, av.value_de, av.value_fr, av.value_en, av.definition_de, None)
        if av.property_code in prop_index:
            g.add((prop_index[av.property_code], INTOP_ONT.hasAllowedValue, au))

    for cp in dd.class_properties:
        if cp.class_code in class_index and cp.property_code in prop_index:
            asg = URIRef(f"{class_index[cp.class_code]}/assignment/{quote(cp.property_code, safe='')}")
            g.add((asg, RDF.type, INTOP_ONT.Assignment))
            g.add((asg, INTOP_ONT.assignedClass, class_index[cp.class_code]))
            g.add((asg, INTOP_ONT.assignedProperty, prop_index[cp.property_code]))
            g.add((asg, INTOP_ONT.isRequired, Literal(bool(cp.is_required), datatype=XSD.boolean)))
            g.add((asg, INTOP_ONT.isWritable, Literal(bool(cp.is_writable), datatype=XSD.boolean)))
            g.add((class_index[cp.class_code], INTOP_ONT.hasProperty, prop_index[cp.property_code]))
            if cp.property_set_name:
                psu = ns['pset'][quote(str(cp.property_set_name), safe='')]
                g.add((psu, RDF.type, INTOP_ONT.PropertySet))
                g.add((psu, SKOS.inScheme, dict_uri))
                g.add((psu, RDFS.label, Literal(cp.property_set_name)))
                g.add((asg, INTOP_ONT.propertySet, psu))
                g.add((class_index[cp.class_code], INTOP_ONT.hasPropertySet, psu))

    documents = getattr(dd, 'documents', []) or []
    document_groups = {}
    for doc in documents:
        group_code = (doc.get('DocumentGroupCode') or '').strip()
        group_name = (doc.get('DocumentGroupName') or doc.get('DocumentGroupLabel') or '').strip()
        if group_code:
            group_uri = ns['document-group'][quote(group_code, safe='')]
            document_groups[group_code] = group_uri
            g.add((group_uri, RDF.type, INTOP_ONT.DocumentGroup))
            g.add((group_uri, SKOS.inScheme, dict_uri))
            if group_name:
                g.add((group_uri, RDFS.label, Literal(group_name, lang='de')))
        doc_uri = URIRef(doc.get('OwnedUri')) if doc.get('OwnedUri') else ns['document'][quote(doc.get('Dokument-ID') or doc.get('Identification') or doc.get('Name') or 'document', safe='')]
        g.add((doc_uri, RDF.type, INTOP_ONT.DocumentReference))
        g.add((doc_uri, SKOS.inScheme, dict_uri))
        if doc.get('DocumentCode') or doc.get('Identification'):
            g.add((doc_uri, DCTERMS.identifier, Literal(doc.get('DocumentCode') or doc.get('Identification'))))
        if doc.get('DocumentLabel') or doc.get('Name'):
            g.add((doc_uri, RDFS.label, Literal(doc.get('DocumentLabel') or doc.get('Name'), lang='de')))
        if doc.get('Dokument URI'):
            g.add((doc_uri, INTOP_ONT.documentUri, URIRef(doc.get('Dokument URI'))))
        if doc.get('Owner'):
            g.add((doc_uri, DCTERMS.publisher, Literal(doc.get('Owner'))))
        if group_code and group_code in document_groups:
            g.add((doc_uri, INTOP_ONT.inDocumentGroup, document_groups[group_code]))
            g.add((document_groups[group_code], INTOP_ONT.hasDocument, doc_uri))

    for cr in dd.concept_relations:
        subj = class_index.get(cr.subject_code) or prop_index.get(cr.subject_code)
        if not subj:
            subj = URIRef(f"{ns['base']}unresolved/{quote(cr.subject_code, safe='')}")
        pred = REL_MAP.get(cr.relation_type, SKOS.relatedMatch)
        g.add((subj, pred, URIRef(cr.related_uri)))
        if cr.notes:
            g.add((subj, RDFS.comment, Literal(cr.notes)))
    return g


def write_trig(dd_paths, outpath=None):
    outpath = Path(outpath or OUTPUT)
    ds = Dataset()
    for prefix, uri in PREFIXES.items():
        ds.bind(prefix, uri)
    total = 0
    for path in dd_paths:
        dd = load_dd(Path(path))
        g = dd_to_graph(dd)
        target = ds.graph(g.identifier)
        for s, p, o in g:
            target.add((s, p, o))
            total += 1
    ds.serialize(destination=str(outpath), format='trig')
    return outpath, total


if __name__ == '__main__':
    base = Path(__file__).resolve().parents[3] / 'HE_SEM_shemaforge'
    paths = [
        base / 'HE_DD_Strukturvorlagev0.1__finalized.xlsx',
    ]
    out, total = write_trig(paths)
    print(f'Wrote: {out} ({out.stat().st_size} bytes, {total} triples)')
