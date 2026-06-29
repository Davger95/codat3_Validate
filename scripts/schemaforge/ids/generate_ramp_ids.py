"""
Stage 1 ramp IDS generator for the current FDK + RTE MVP.
Generates one IDS for IfcRamp using selected properties from both dictionaries,
retrieved from the RDF semantic graph (TriG), not from Excel.
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from rdflib import Dataset
from rdflib.namespace import RDFS, SKOS, RDF, XSD

WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE / 'scripts' / 'schemaforge'))

from config import INTOP_ONT
from ids.ids_mapper import map_property, IDSSpecificationSpec
from ids.ids_builder import build_ids
from ids.ids_writer import write_ids, write_ids_summary
from ids.graph_retriever import ClassInfo, PropertyInfo, AllowedValueInfo

TRIG_PATH = WORKSPACE / 'SchemaForge_output' / 'dd_mvp_converted.trig'
OUT_DIR = WORKSPACE / 'SchemaForge_output' / 'ids'

RTE_CLASS = 'https://rte.voev.ch/26201/class/rampe'
FDK_CLASS = 'https://he-sem.ch/class/obj-hb-551'

TARGET_PROPS = [
    'https://he-sem.ch/property/pty-380680',
    'https://he-sem.ch/property/pty-380678',
    'https://he-sem.ch/property/pty-380679',
    'https://rte.voev.ch/26201/property/is-covered',
    'https://rte.voev.ch/26201/property/station-class',
    'https://rte.voev.ch/26201/property/operation-mode',
    'https://rte.voev.ch/26201/property/mean-illuminance-em',
    'https://rte.voev.ch/26201/property/uniformity-u0',
    'https://rte.voev.ch/26201/property/non-uniformity-ud',
    'https://rte.voev.ch/26201/property/glare-rating-limit-grl',
    'https://rte.voev.ch/26201/property/colour-rendering-index-ra',
]


def lit(ds, s, p):
    for o in ds.objects(s, p):
        return str(o)
    return None


def bool_lit(ds, s, p):
    for o in ds.objects(s, p):
        if getattr(o, 'datatype', None) == XSD.boolean:
            return bool(o.toPython())
        return str(o).lower() == 'true'
    return False


def labels(ds, s):
    vals = list(ds.objects(s, RDFS.label))
    bylang = {}
    for v in vals:
        bylang[getattr(v, 'language', None)] = str(v)
    return bylang


def class_info(ds, uri):
    lbl = labels(ds, uri)
    return ClassInfo(
        uri=uri,
        label=lbl.get('de') or lbl.get('en') or uri.split('/')[-1],
        ifc_entity=lit(ds, uri, INTOP_ONT.ifcEntityCode) or 'IfcProduct',
        ifc_predefined_type=lit(ds, uri, INTOP_ONT.ifcPredefinedType),
        ifc_class_uri=lit(ds, uri, INTOP_ONT.ifcClassUri),
    )


def property_info(ds, class_uri, prop_uri):
    lbl = labels(ds, prop_uri)
    p = PropertyInfo(
        uri=prop_uri,
        label=lbl.get('de') or lbl.get('en') or prop_uri.split('/')[-1],
        data_type=lit(ds, prop_uri, INTOP_ONT.dataType) or 'STRING',
        pset_name=lit(ds, prop_uri, INTOP_ONT.propertySetName),
        pset_uri=None,
        ifc_prop_uri=lit(ds, prop_uri, INTOP_ONT.ifcPropertyUri),
        ifc_pset_uri=lit(ds, prop_uri, INTOP_ONT.ifcPsetUri),
        is_required=False,
        allowed_values=[],
        assign_uri=None,
    )
    # find assignment linking this class and property
    for a in ds.subjects(INTOP_ONT.assignedClass, class_uri):
        if (a, INTOP_ONT.assignedProperty, prop_uri) in ds:
            p.assign_uri = str(a)
            p.pset_name = lit(ds, a, INTOP_ONT.propertySetName) or p.pset_name
            p.pset_uri = lit(ds, a, INTOP_ONT.propertySet)
            p.is_required = bool_lit(ds, a, INTOP_ONT.isRequired)
            break
    # fallback: infer from class hasProperty relationship if assignments were not materialized in RDF
    if not p.assign_uri and (class_uri, INTOP_ONT.hasProperty, prop_uri) in ds:
        p.assign_uri = f'{class_uri}/inferred-assignment/{prop_uri.split('/')[-1]}'
        p.is_required = True
    # allowed values
    seen = set()
    for av in ds.objects(prop_uri, INTOP_ONT.hasAllowedValue):
        code = lit(ds, av, INTOP_ONT.valueCode)
        if code and code not in seen:
            seen.add(code)
            avlbl = labels(ds, av)
            p.allowed_values.append(AllowedValueInfo(code=code, label=avlbl.get('de') or avlbl.get('en')))
    return p


def build_ramp_ids():
    ds = Dataset()
    ds.parse(TRIG_PATH, format='trig')

    rte = class_info(ds, RTE_CLASS)
    fdk = class_info(ds, FDK_CLASS)
    if rte.ifc_entity == 'IfcProduct':
        for o in ds.objects(RTE_CLASS, SKOS.closeMatch):
            if str(o).split('/')[-1] == 'IfcRamp':
                rte.ifc_entity = 'IfcRamp'
    if fdk.ifc_entity == 'IfcProduct':
        for o in ds.objects(FDK_CLASS, SKOS.closeMatch):
            if str(o).split('/')[-1] == 'IfcRamp':
                fdk.ifc_entity = 'IfcRamp'

    # applicability anchored to exactMatch pair; use IfcRamp from RTE/FDK
    properties = []
    for prop_uri in TARGET_PROPS:
        if prop_uri.startswith('https://he-sem.ch/property/'):
            properties.append(property_info(ds, FDK_CLASS, prop_uri))
        else:
            properties.append(property_info(ds, RTE_CLASS, prop_uri))

    ids_props = [map_property(p) for p in properties]
    spec = IDSSpecificationSpec(
        spec_name='Ramp — FDK + RTE 26201 MVP Requirements',
        ifc_entity=rte.ifc_entity or fdk.ifc_entity or 'IfcRamp',
        ifc_predefined_type=rte.ifc_predefined_type or fdk.ifc_predefined_type,
        properties=ids_props,
        description=(
            'Composite IDS for ramp based on exactMatch-linked concepts '
            f'{FDK_CLASS} and {RTE_CLASS}. Includes selected FDK identification/project properties '
            'and RTE context + lighting requirement properties.'
        ),
    )

    ids_doc = build_ids(
        spec_list=[spec],
        title='Ramp_MVP_FDK_RTE26201',
        version='0.1.0',
        description='IDS generated from HE-SEM RDF graph for ramp MVP (FDK + RTE 26201).',
        author='datadict@he-sem.ch',
        purpose='Cross-dictionary BIM validation MVP',
    )

    ids_path = OUT_DIR / 'Ramp_MVP_FDK_RTE26201.ids'
    summary_path = OUT_DIR / 'Ramp_MVP_FDK_RTE26201_summary.md'
    write_ids(ids_doc, ids_path, validate=True)
    write_ids_summary(ids_doc, summary_path)
    return ids_path, summary_path, spec, properties


if __name__ == '__main__':
    ids_path, summary_path, spec, properties = build_ramp_ids()
    print('Wrote IDS:', ids_path)
    print('Wrote summary:', summary_path)
    print('IFC entity:', spec.ifc_entity)
    print('Property count:', len(properties))
    for p in properties:
        print('-', p.pset_name, '/', p.label, '|', p.data_type, '| required=', p.is_required, '| allowed=', len(p.allowed_values))
