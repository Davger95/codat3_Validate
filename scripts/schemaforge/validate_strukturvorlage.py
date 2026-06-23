from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import openpyxl

from readers.excel_reader import load_dd

WORKSPACE = Path('/home/Dave/.openclaw/workspace-datadict')
BSDD_TTL = Path('/home/Dave/.openclaw/shared/ontologies/bsdd/ifc4.3-bsdd-harvested-official-api.ttl.tmp')
BSDD_URI_CACHE = Path('/home/Dave/.openclaw/shared/ontologies/bsdd/ifc4.3-uri-cache.json')
VALID_BSDD_URI_PREFIXES = (
    'https://identifier.buildingsmart.org/uri/buildingsmart/ifc/',
)
REQUIRED_SHEETS = [
    'Dictionary',
    'Klassen',
    'Merkmale_Merkmalsgruppen',
    'Dokumente_Dokumentgruppen',
    'KlassenMerkmal',
]
REQUIRED_SHEETS_V20260619 = [
    'Objekte',
    'Merkmale_Merkmalsgruppen',
    'Wertekatalog',
    'Dokumente_Dokumentgruppen',
    'Data Template AreaMgmt',
]
OPTIONAL_SHEETS = ['ConceptRelation']
ALLOWED_LIFECYCLE = {'Preview', 'Active', 'Inactive'}
ALLOWED_BASE_TYPES = {'STRING', 'INTEGER', 'REAL', 'BOOLEAN', 'TIME', 'DATETIME'}
ALLOWED_REL_TYPES = {
    'skos:exactMatch',
    'skos:closeMatch',
    'skos:narrowMatch',
    'skos:broadMatch',
    'skos:relatedMatch',
    'owl:sameAs',
}
ALLOWED_CONCEPT_TYPES = {'Class', 'Property', 'AllowedValue', 'PropertySet', 'Enumeration', 'Other'}
SEMVER_RE = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')


@dataclass
class Finding:
    level: str
    code: str
    message: str
    sheet: str | None = None
    cell: str | None = None
    row: int | None = None


class Validator:
    def __init__(self, workbook_path: Path):
        self.workbook_path = workbook_path
        self.findings: list[Finding] = []
        self.normalizations: list[dict] = []
        self.wb = openpyxl.load_workbook(workbook_path, data_only=True)
        self.dd = None
        self.ifc_uri_set = None
        self.dd_loaded = False
        self.ifc_uri_set_loaded = False

    def get_dd(self):
        if self.dd is None:
            self.dd = load_dd(self.workbook_path)
            self.dd_loaded = True
        return self.dd

    def get_ifc_uri_set(self) -> set[str]:
        if self.ifc_uri_set is None:
            self.ifc_uri_set = self._load_ifc_uri_set()
            self.ifc_uri_set_loaded = True
        return self.ifc_uri_set

    def add(self, level: str, code: str, message: str, sheet: str | None = None, cell: str | None = None, row: int | None = None):
        self.findings.append(Finding(level, code, message, sheet, cell, row))

    def add_normalization(self, sheet: str, row: int | None, column: str | None, original_value, normalized_value, reason: str, normalization_kind: str, safe_auto_normalization: bool = True):
        self.normalizations.append({
            'sheet': sheet,
            'row': row,
            'column': column,
            'original_value': original_value,
            'normalized_value': normalized_value,
            'reason': reason,
            'normalization_kind': normalization_kind,
            'safe_auto_normalization': safe_auto_normalization,
        })

    def _load_ifc_uri_set(self) -> set[str]:
        if BSDD_URI_CACHE.exists():
            try:
                payload = json.loads(BSDD_URI_CACHE.read_text())
                return set(payload.get('uris', []))
            except Exception as e:
                self.add('warning', 'ifc_cache_load_failed', f'Failed to load IFC URI cache {BSDD_URI_CACHE}: {e}')
        if not BSDD_TTL.exists():
            self.add('warning', 'ifc_reference_missing', f'Authoritative IFC reference TTL not found: {BSDD_TTL}')
            return set()
        uri_re = re.compile(r'https://identifier\.buildingsmart\.org/uri/buildingsmart/ifc/4\.3(?:\.0)?/[^\s<>"]+')
        uris = set()
        with BSDD_TTL.open('r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                for m in uri_re.findall(line):
                    uris.add(m)
        return uris

    def validate(self):
        self.validate_required_sheets()
        self.validate_dictionary()
        self.validate_klassen()
        self.validate_properties()
        self.validate_documents()
        self.validate_matrix()
        self.validate_concept_relations()
        self.validate_pipeline_minimums()
        return self.build_report()

    def is_v20260619_template(self) -> bool:
        return {'Objekte', 'Wertekatalog', 'Data Template AreaMgmt'}.issubset(set(self.wb.sheetnames))

    def validate_required_sheets(self):
        required = REQUIRED_SHEETS_V20260619 if self.is_v20260619_template() else REQUIRED_SHEETS
        missing = [s for s in required if s not in self.wb.sheetnames]
        for sheet in missing:
            self.add('error', 'missing_sheet', f'Missing required sheet: {sheet}', sheet=sheet)

    def _dict_rows(self) -> dict[str, tuple[str | None, int]]:
        ws = self.wb['Dictionary']
        rows = {}
        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            field = row[0] if len(row) > 0 else None
            value = row[1] if len(row) > 1 else None
            if field is not None:
                rows[str(field).strip()] = (None if value is None else str(value).strip(), i)
        return rows

    def validate_dictionary(self):
        if 'Dictionary' not in self.wb.sheetnames:
            return
        rows = self._dict_rows()
        required = [
            'OrganizationCode', 'DictionaryCode', 'DictionaryName (DE)', 'DictionaryName (FR)',
            'DictionaryVersion', 'DictionaryUri', 'LifecycleStatus', 'Owner / Publisher'
        ]
        for key in required:
            value_row = rows.get(key)
            if not value_row or not value_row[0]:
                self.add('error', 'missing_dictionary_field', f'Missing required dictionary value: {key}', sheet='Dictionary', row=value_row[1] if value_row else None)
        status = (rows.get('LifecycleStatus') or [None])[0]
        if status and status not in ALLOWED_LIFECYCLE:
            self.add('error', 'invalid_lifecycle', f'Invalid LifecycleStatus: {status}', sheet='Dictionary')
        version = (rows.get('DictionaryVersion') or [None])[0]
        if version and not SEMVER_RE.match(version):
            self.add('error', 'invalid_semver', f'DictionaryVersion must be semantic version, got: {version}', sheet='Dictionary')
        uri = (rows.get('DictionaryUri') or [None])[0]
        if uri and not self.is_absolute_uri(uri):
            self.add('error', 'invalid_uri', f'DictionaryUri is not a valid absolute IRI: {uri}', sheet='Dictionary')

    def is_valid_bsdd_identifier_uri(self, value: str) -> bool:
        return any(value.startswith(prefix) for prefix in VALID_BSDD_URI_PREFIXES)

    @staticmethod
    def slugify(value: str | None) -> str:
        if not value:
            return ''
        s = str(value).strip().lower()
        s = re.sub(r'[^a-z0-9]+', '-', s)
        s = re.sub(r'-+', '-', s).strip('-')
        return s

    def parse_allowed_list(self, raw: str | None, sheet: str | None = None, row: int | None = None, column: str | None = None) -> list[str]:
        if not raw:
            return []
        txt = str(raw).strip()
        if txt.startswith('[') and txt.endswith(']'):
            try:
                parsed = json.loads(txt)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        parts = [p.strip().strip('"').strip("'") for p in re.split(r'[;,]', txt) if p and p.strip()]
        normalized = [p for p in parts if p]
        normalized_json = json.dumps(normalized, ensure_ascii=False)
        if txt != normalized_json and sheet:
            self.add_normalization(sheet, row, column, txt, normalized_json, 'Legacy delimiter-based list normalized to JSON-style list for validation comparison', 'list-format-normalization', True)
        return normalized

    def validate_klassen(self):
        sheet_name = 'Objekte' if self.is_v20260619_template() and 'Objekte' in self.wb.sheetnames else 'Klassen'
        if sheet_name not in self.wb.sheetnames:
            return
        ws = self.wb[sheet_name]
        seen_codes = set()
        dd = self.get_dd()
        ifc_uri_set = self.get_ifc_uri_set()
        document_source_codes = {d.get('SourceCode') for d in getattr(dd, 'documents', []) if d.get('SourceCode')}
        start_row = 10
        for idx, row in enumerate(ws.iter_rows(min_row=start_row, values_only=True), start=start_row):
            if not any(v is not None and str(v).strip() for v in row):
                continue
            if self.is_v20260619_template():
                obj_id = self._cell(row, 9)
                obj_einordnung = self._cell(row, 10)
                bezeichnung = self._cell(row, 11)
                designation = self._cell(row, 12)
                beschreibung = self._cell(row, 13)
                description = self._cell(row, 14)
                ifc_uri = self._cell(row, 16)
                ifc_obj = self._cell(row, 17)
                ifc_type = self._cell(row, 18)
                predefined = None
                source = None
                identification = None
                final_name = None
            else:
                obj_id = self._cell(row, 7)
                bezeichnung = self._cell(row, 9)
                designation = self._cell(row, 10)
                beschreibung = self._cell(row, 11)
                description = self._cell(row, 12)
                ifc_uri = self._cell(row, 13)
                ifc_obj = self._cell(row, 14)
                ifc_type = self._cell(row, 15)
                predefined = self._cell(row, 16)
                source = self._cell(row, 20)
                identification = self._cell(row, 23)
                final_name = self._cell(row, 24)
                obj_einordnung = self._cell(row, 8)
            if not obj_id:
                derived_id = self.slugify(designation or bezeichnung)
                if derived_id:
                    self.add('warning', 'missing_class_code', f'Klassen row missing Objekt-ID; derivable suggested ID: {derived_id}', sheet='Klassen', row=idx)
                    self.add_normalization('Klassen', idx, 'Objekt-ID', obj_id, derived_id, 'Missing class ID is derivable from Designation/Bezeichnung', 'derived-id-suggestion', True)
                    obj_id = derived_id
                else:
                    self.add('error', 'missing_class_code', 'Klassen row missing Objekt-ID and no derivable Designation/Bezeichnung is available', sheet=sheet_name, row=idx)
            elif obj_id in seen_codes:
                self.add('error', 'duplicate_class_code', f'Duplicate Objekt-ID: {obj_id}', sheet=sheet_name, row=idx)
            else:
                seen_codes.add(obj_id)
            if not (bezeichnung or designation):
                self.add('error', 'missing_class_label', 'Klassen row missing Bezeichnung/Designation', sheet=sheet_name, row=idx)
            if not (beschreibung or description):
                self.add('error', 'missing_class_definition', 'Klassen row missing Beschreibung/Description', sheet=sheet_name, row=idx)
            if not obj_einordnung:
                self.add('warning', 'missing_objekt_einordnung', 'Klassen row missing Objekt-Einordnung', sheet=sheet_name, row=idx)
            if not ifc_uri:
                self.add('error', 'missing_ifc_uri', 'Klassen row missing IFC URI', sheet=sheet_name, row=idx)
            else:
                if not self.is_absolute_uri(ifc_uri):
                    self.add('error', 'invalid_ifc_uri', f'Invalid IFC URI: {ifc_uri}', sheet=sheet_name, row=idx)
                elif not self.is_valid_bsdd_identifier_uri(ifc_uri):
                    self.add('error', 'invalid_ifc_uri_namespace', f'IFC URI is not in a valid buildingSMART/bSDD identifier namespace: {ifc_uri}', sheet=sheet_name, row=idx)
                elif ifc_uri_set and ifc_uri not in ifc_uri_set:
                    self.add('error', 'unknown_ifc_uri', f'IFC URI not found in authoritative bSDD harvest: {ifc_uri}', sheet=sheet_name, row=idx)
            if not ifc_obj:
                self.add('error', 'missing_ifc_object_entity', 'Klassen row missing IfcObject Entity', sheet=sheet_name, row=idx)
            if not ifc_type:
                self.add('warning', 'missing_ifc_type_object_entity', 'IfcTypeObject Entity is missing; this may be acceptable if mapping exists only on object level', sheet=sheet_name, row=idx)
            if not predefined:
                self.add('warning', 'missing_predefined_type', 'PredefinedType is missing; this may be acceptable if only object-level mapping is intended', sheet=sheet_name, row=idx)
            if not self.is_v20260619_template():
                classification_in_use = bool(source or identification or final_name)
                if not source:
                    self.add('error', 'missing_source', 'Klassen row missing Source. Provide a registered source code or use Organisation if no external source exists/you do not know it.', sheet=sheet_name, row=idx)
                elif source != 'Organisation' and document_source_codes and source not in document_source_codes:
                    self.add('error', 'unknown_source_code', f'Klassen.Source not registered in Dokumente_Dokumentgruppen.SourceCode: {source}. Add the source formally or use Organisation.', sheet=sheet_name, row=idx)
                if classification_in_use and source and source != 'Organisation' and not identification:
                    self.add('warning', 'missing_identification', 'Classification source is given but Identification is missing. Please add it if applicable, otherwise ignore.', sheet=sheet_name, row=idx)
                if classification_in_use and (source or identification) and not final_name:
                    self.add('warning', 'missing_classification_name', 'Classification section is in use but final Name column is missing.', sheet=sheet_name, row=idx)

    def validate_properties(self):
        if 'Merkmale_Merkmalsgruppen' not in self.wb.sheetnames:
            return
        ws = self.wb['Merkmale_Merkmalsgruppen']
        ifc_uri_set = self.get_ifc_uri_set()
        seen_codes = set()
        if self.is_v20260619_template() and 'Wertekatalog' in self.wb.sheetnames:
            value_ids = set()
            vws = self.wb['Wertekatalog']
            for vr in vws.iter_rows(min_row=10, values_only=True):
                vid = self._cell(vr, 5)
                if vid:
                    value_ids.add(vid)
        else:
            value_ids = set()
        start_row = 8 if self.is_v20260619_template() else 4
        for idx, row in enumerate(ws.iter_rows(min_row=start_row, values_only=True), start=start_row):
            if not any(v is not None and str(v).strip() for v in row):
                continue
            if self.is_v20260619_template():
                prop_code = self._cell(row, 5)
                merkmal = self._cell(row, 6)
                prop_en = self._cell(row, 7)
                data_type = self._cell(row, 10)
                data_type_ifc = self._cell(row, 11)
                value_list_id = self._cell(row, 12)
                value_list = None
                ifc_property_uri = self._cell(row, 14)
                ifc_pset = self._cell(row, 15)
                ifc_qto = self._cell(row, 16)
                custom_pset = self._cell(row, 17)
                local_group = self._cell(row, 17)
            else:
                prop_code = self._cell(row, 4)
                merkmal = self._cell(row, 5)
                prop_en = self._cell(row, 6)
                data_type = self._cell(row, 9)
                data_type_ifc = self._cell(row, 10)
                value_list_id = self._cell(row, 11)
                value_list = self._cell(row, 12)
                ifc_property_uri = self._cell(row, 14)
                ifc_pset = self._cell(row, 15)
                ifc_qto = self._cell(row, 16)
                custom_pset = self._cell(row, 17)
                local_group = self._cell(row, 20)
            if not prop_code:
                self.add('error', 'missing_property_code', 'Property row missing Merkmal-ID', sheet='Merkmale_Merkmalsgruppen', row=idx)
            elif prop_code in seen_codes:
                self.add('error', 'duplicate_property_code', f'Duplicate Merkmal-ID: {prop_code}', sheet='Merkmale_Merkmalsgruppen', row=idx)
            else:
                seen_codes.add(prop_code)
            if not merkmal:
                self.add('error', 'missing_property_label_de', 'Property row missing Merkmal', sheet='Merkmale_Merkmalsgruppen', row=idx)
            if not prop_en:
                self.add('error', 'missing_property_label_en', 'Property row missing Property', sheet='Merkmale_Merkmalsgruppen', row=idx)
            if not data_type:
                self.add('error', 'missing_data_type', 'Property row missing DataType (Base Type)', sheet='Merkmale_Merkmalsgruppen', row=idx)
            elif data_type.upper() not in ALLOWED_BASE_TYPES:
                self.add('error', 'invalid_data_type', f'Invalid DataType (Base Type): {data_type}', sheet='Merkmale_Merkmalsgruppen', row=idx)
            if not data_type_ifc:
                self.add('error', 'missing_ifc_data_type', 'Property row missing DataType (IFC)', sheet='Merkmale_Merkmalsgruppen', row=idx)
            if value_list_id and self.is_v20260619_template() and value_ids:
                if value_list_id not in value_ids:
                    self.add('error', 'unknown_value_list_id', f'Werteliste-ID {value_list_id} is not registered in Wertekatalog.', sheet='Merkmale_Merkmalsgruppen', row=idx)
            if not any([ifc_pset, ifc_qto, custom_pset, local_group]):
                self.add('error', 'missing_property_set_locator', 'Property row has no IfcPropertySet / IfcQuantitySet reference and no Merkmalsgruppe. Provide an official IFC set reference if applicable, otherwise provide Merkmalsgruppe.', sheet='Merkmale_Merkmalsgruppen', row=idx)
            if not ifc_property_uri:
                self.add('warning', 'missing_ifc_property_uri_reference', 'Official IFC property URI is empty. Provide an official IFC property URI if applicable.', sheet='Merkmale_Merkmalsgruppen', row=idx)
            if not ifc_pset and not ifc_qto:
                self.add('warning', 'missing_ifc_property_set_reference', 'Official IfcPropertySet/IfcQuantitySet reference is empty. Provide an official IFC set reference if applicable, otherwise use Merkmalsgruppe.', sheet='Merkmale_Merkmalsgruppen', row=idx)
            for uri_label, uri_value in [('IfcPropertySet (Pset)', ifc_pset), ('IfcQuantitySet (Qto)', ifc_qto)]:
                if uri_value and uri_value.startswith('http'):
                    if not self.is_absolute_uri(uri_value):
                        self.add('error', 'invalid_ifc_linked_uri', f'{uri_label} is not a valid absolute IRI: {uri_value}', sheet='Merkmale_Merkmalsgruppen', row=idx)
                    elif not self.is_valid_bsdd_identifier_uri(uri_value):
                        self.add('error', 'invalid_ifc_linked_uri_namespace', f'{uri_label} is not in a valid buildingSMART/bSDD identifier namespace: {uri_value}', sheet='Merkmale_Merkmalsgruppen', row=idx)
                    elif ifc_uri_set and uri_value not in ifc_uri_set:
                        self.add('error', 'unknown_ifc_linked_uri', f'{uri_label} not found in authoritative bSDD harvest: {uri_value}', sheet='Merkmale_Merkmalsgruppen', row=idx)
            expected_value_list_id = f"{self.slugify(prop_en or merkmal).replace('-', '_')}_enum" if (prop_en or merkmal) else None
            if value_list_id:
                if expected_value_list_id and value_list_id != expected_value_list_id:
                    self.add('warning', 'noncanonical_value_list_id', f'Werteliste-ID is present but differs from canonical generated form {expected_value_list_id}', sheet='Merkmale_Merkmalsgruppen', row=idx)
            elif value_list or (self.is_v20260619_template() and value_ids):
                self.add('warning', 'missing_value_list_id', f'Werteliste-ID is missing; derivable generated ID: {expected_value_list_id}', sheet='Merkmale_Merkmalsgruppen', row=idx)
                if expected_value_list_id:
                    self.add_normalization('Merkmale_Merkmalsgruppen', idx, 'Werteliste-ID', value_list_id, expected_value_list_id, 'Missing Werteliste-ID is derivable from Property/Merkmal', 'derived-enumeration-id', True)
            if value_list:
                parsed = self.parse_allowed_list(value_list, sheet='Merkmale_Merkmalsgruppen', row=idx, column='Werteliste')
                if len(parsed) != len(set(parsed)):
                    self.add('error', 'duplicate_enumeration_values', f'Werteliste contains duplicate values for {prop_code}', sheet='Merkmale_Merkmalsgruppen', row=idx)

    def validate_documents(self):
        dd = self.get_dd()
        docs = getattr(dd, 'documents', [])
        seen_doc_ids = set()
        seen_doc_codes = set()
        seen_group_map = {}
        for i, doc in enumerate(docs, start=9):
            source_code = doc.get('SourceCode')
            doc_id = doc.get('Dokument-ID')
            doc_name = doc.get('Dokument Name')
            revision = doc.get('Revision')
            owner = doc.get('Owner')
            doc_code = doc.get('DocumentCode')
            doc_label = doc.get('DocumentLabel')
            group_code = doc.get('DocumentGroupCode')
            group_label = doc.get('DocumentGroupName') or doc.get('DocumentGroupLabel')
            if not source_code:
                self.add('error', 'missing_source_code', 'Document row missing SourceCode. Provide a registered source code or use Organisation.', sheet='Dokumente_Dokumentgruppen', row=i)
            elif source_code != 'Organisation':
                seen_doc_ids.add(doc_id) if doc_id else None
            if not doc_name:
                self.add('error', 'missing_document_name', 'Document row missing Dokument Name', sheet='Dokumente_Dokumentgruppen', row=i)
            if revision is None or str(revision).strip() == '':
                self.add('error', 'missing_revision', 'Document row missing Revision', sheet='Dokumente_Dokumentgruppen', row=i)
            if not owner:
                self.add('error', 'missing_owner', 'Document row missing Owner', sheet='Dokumente_Dokumentgruppen', row=i)
            if not doc_code:
                self.add('error', 'missing_document_code', 'Document row missing DocumentCode', sheet='Dokumente_Dokumentgruppen', row=i)
            elif doc_code in seen_doc_codes:
                self.add('error', 'duplicate_document_code', f'Duplicate DocumentCode: {doc_code}', sheet='Dokumente_Dokumentgruppen', row=i)
            else:
                seen_doc_codes.add(doc_code)
            if not group_code:
                self.add('error', 'missing_document_group_code', 'Document row missing DocumentGroupCode', sheet='Dokumente_Dokumentgruppen', row=i)
            if not group_label:
                self.add('error', 'missing_document_group_label', 'Document row missing DocumentGroupLabel', sheet='Dokumente_Dokumentgruppen', row=i)
            elif group_code:
                prev = seen_group_map.get(group_code)
                if prev and prev != group_label:
                    self.add('error', 'inconsistent_group_label', f'DocumentGroupCode {group_code} maps to multiple labels: {prev} / {group_label}', sheet='Dokumente_Dokumentgruppen', row=i)
                seen_group_map[group_code] = group_label
            doc_uri = doc.get('Dokument URI')
            if doc_uri and not self.is_absolute_uri(doc_uri):
                self.add('error', 'invalid_document_uri', f'Dokument URI is invalid: {doc_uri}', sheet='Dokumente_Dokumentgruppen', row=i)

    def validate_matrix(self):
        matrix_sheet = 'Data Template AreaMgmt' if self.is_v20260619_template() and 'Data Template AreaMgmt' in self.wb.sheetnames else 'KlassenMerkmal'
        if matrix_sheet not in self.wb.sheetnames:
            return
        ws = self.wb[matrix_sheet]
        dd = self.get_dd()
        class_codes = {c.code for c in dd.classes}
        property_name_de = {p.name_de: p.code for p in dd.properties if p.name_de}
        property_name_en = {p.name_en: p.code for p in dd.properties if p.name_en}
        property_codes_registered = {p.code for p in dd.properties if p.code}
        registered_property_sets = set()
        for p in dd.properties:
            if getattr(p, 'ifc_pset_uri', None):
                registered_property_sets.add(getattr(p, 'ifc_pset_uri'))
            if getattr(p, 'property_set_name', None):
                registered_property_sets.add(getattr(p, 'property_set_name'))
            if getattr(p, 'raw_ifc_qto', None):
                registered_property_sets.add(getattr(p, 'raw_ifc_qto'))
            if getattr(p, 'merkmalsgruppe', None):
                registered_property_sets.add(getattr(p, 'merkmalsgruppe'))
        if self.is_v20260619_template():
            property_cols = []
            for col_idx in range(5, ws.max_column + 1):
                prop_code = self._cell([ws.cell(3, col_idx).value], 1)
                if prop_code:
                    property_cols.append((col_idx, prop_code))
                    if prop_code not in property_codes_registered:
                        self.add('error', 'matrix_unknown_merkmal_id', f'Data Template AreaMgmt references unknown Merkmal-ID in row 3: {prop_code}', sheet=matrix_sheet, row=3)
            if not property_cols:
                self.add('error', 'matrix_missing_property_columns', 'Data Template AreaMgmt has no property IDs in row 3 from column 5 onward', sheet=matrix_sheet, row=3)
            for ridx in range(6, ws.max_row + 1):
                class_code = self._cell([ws.cell(ridx, 1).value], 1)
                class_label = self._cell([ws.cell(ridx, 2).value], 1)
                if not any(self._cell([ws.cell(ridx, c).value], 1) for c in range(1, ws.max_column + 1)):
                    continue
                if not class_code:
                    continue
                if class_code not in class_codes:
                    self.add('error', 'matrix_unknown_class', f'Data Template AreaMgmt row references unknown class/object ID: {class_code}', sheet=matrix_sheet, row=ridx)
                for col_idx, prop_code in property_cols:
                    cell = self._cell([ws.cell(ridx, col_idx).value], 1)
                    if not cell:
                        continue
                    if prop_code not in property_codes_registered:
                        continue
                    if cell.lower() != 'x':
                        allowed = self.allowed_values_for_property(prop_code)
                        overrides = self.parse_allowed_list(cell, sheet=matrix_sheet, row=ridx, column=f'col-{col_idx}')
                        allowed_cmp = {a.strip().casefold() for a in allowed}
                        overrides_cmp = {o.strip().casefold() for o in overrides}
                        if allowed and not overrides_cmp.issubset(allowed_cmp):
                            self.add('error', 'invalid_allowed_values_override', f'This object-specific restriction contains values {overrides} that are not listed in the property\'s official allowed values for {prop_code}. Please correct the override or add the missing value to the property\'s allowed values.', sheet=matrix_sheet, row=ridx)
            return
        row5 = [self._norm(v) for v in next(ws.iter_rows(min_row=5, max_row=5, values_only=True))]
        object_ids = []
        for idx, obj_id in enumerate(row5, start=1):
            if idx >= 8 and obj_id and obj_id != 'Objekt-ID':
                object_ids.append((idx, obj_id))
                if obj_id not in class_codes:
                    self.add('error', 'matrix_unknown_class', f'KlassenMerkmal row 5 references unknown class code: {obj_id}', sheet='KlassenMerkmal', row=5)
        if not object_ids:
            self.add('error', 'matrix_missing_object_columns', 'KlassenMerkmal has no object IDs in row 5 from column 8 onward', sheet='KlassenMerkmal', row=5)
        for ridx, row in enumerate(ws.iter_rows(min_row=9, values_only=True), start=9):
            vals = list(row)
            if not any(v is not None and str(v).strip() for v in vals):
                continue
            matrix_merkmal_id = self._cell(vals, 2)
            pset = self._cell(vals, 3)
            merkmal = self._cell(vals, 4)
            prop_en = self._cell(vals, 5)
            if not (matrix_merkmal_id or pset or merkmal or prop_en):
                continue
            if not matrix_merkmal_id:
                self.add('error', 'matrix_missing_merkmal_id', 'KlassenMerkmal row is missing Merkmal-ID; it must reference a registered property identifier from Merkmale_Merkmalsgruppen.', sheet='KlassenMerkmal', row=ridx)
                continue
            if matrix_merkmal_id not in property_codes_registered:
                self.add('error', 'matrix_unknown_merkmal_id', f'KlassenMerkmal row references unknown Merkmal-ID: {matrix_merkmal_id}', sheet='KlassenMerkmal', row=ridx)
                continue
            if pset and pset not in registered_property_sets:
                self.add('error', 'unknown_property_set_reference', f'KlassenMerkmal PropertySet is not registered in Merkmale_Merkmalsgruppen as IfcPropertySet, IfcQuantitySet, or Merkmalsgruppe: {pset}', sheet='KlassenMerkmal', row=ridx)
            prop_code = matrix_merkmal_id
            if prop_en and property_name_en.get(prop_en) and property_name_en.get(prop_en) != prop_code:
                self.add('warning', 'matrix_property_name_mismatch', f'Property (EN) does not match the registered Merkmal-ID {prop_code}', sheet='KlassenMerkmal', row=ridx)
            if merkmal and property_name_de.get(merkmal) and property_name_de.get(merkmal) != prop_code:
                self.add('warning', 'matrix_property_label_mismatch', f'Merkmal (DE) does not match the registered Merkmal-ID {prop_code}', sheet='KlassenMerkmal', row=ridx)
            for col_idx, class_code in object_ids:
                cell = self._cell(vals, col_idx)
                if not cell:
                    continue
                if cell.lower() != 'x':
                    allowed = self.allowed_values_for_property(prop_code)
                    overrides = self.parse_allowed_list(cell, sheet='KlassenMerkmal', row=ridx, column=f'object-col-{col_idx}')
                    allowed_cmp = {a.strip().casefold() for a in allowed}
                    overrides_cmp = {o.strip().casefold() for o in overrides}
                    if allowed and not overrides_cmp.issubset(allowed_cmp):
                        self.add('error', 'invalid_allowed_values_override', f'This class-specific restriction contains values {overrides} that are not listed in the property\'s official allowed values for {prop_code}. Please correct the override or add the missing value to the property\'s allowed values.', sheet='KlassenMerkmal', row=ridx)

    def validate_concept_relations(self):
        dd = self.get_dd()
        for idx, cr in enumerate(dd.concept_relations, start=5):
            if cr.concept_type and cr.concept_type not in ALLOWED_CONCEPT_TYPES:
                self.add('error', 'invalid_concept_type', f'Invalid ConceptType: {cr.concept_type}', sheet='ConceptRelation', row=idx)
            if cr.relation_type not in ALLOWED_REL_TYPES:
                self.add('error', 'invalid_relation_type', f'Invalid RelationType: {cr.relation_type}', sheet='ConceptRelation', row=idx)
            if cr.related_uri and not self.is_absolute_uri(cr.related_uri):
                self.add('error', 'invalid_related_uri', f'Invalid RelatedConceptUri: {cr.related_uri}', sheet='ConceptRelation', row=idx)

    def validate_pipeline_minimums(self):
        dd = self.get_dd()
        if len(dd.classes) < 1:
            self.add('error', 'minimum_classes', 'At least one valid class row is required')
        if len(dd.properties) < 1:
            self.add('error', 'minimum_properties', 'At least one valid property row is required')
        if len(dd.class_properties) < 1:
            self.add('error', 'minimum_assignments', 'At least one valid class-property assignment is required')
        if len(getattr(dd, 'documents', [])) < 1:
            self.add('error', 'minimum_documents', 'At least one document row is required for full source-governed output')

    def allowed_values_for_property(self, prop_code: str) -> list[str]:
        dd = self.get_dd()
        for p in dd.properties:
            if p.code == prop_code and p.enumeration_values:
                return self.parse_allowed_list(p.enumeration_values)
        return []

    @staticmethod
    def is_absolute_uri(value: str) -> bool:
        try:
            parsed = urlparse(value)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    @staticmethod
    def _cell(row, idx_1based: int):
        if idx_1based - 1 < len(row):
            v = row[idx_1based - 1]
            if v is None:
                return None
            s = str(v).strip()
            return s if s else None
        return None

    @staticmethod
    def _norm(v):
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    def build_report(self):
        errors = [f for f in self.findings if f.level == 'error']
        warnings = [f for f in self.findings if f.level == 'warning']
        parser_valid = len([e for e in errors if e.code in {
            'missing_sheet', 'missing_dictionary_field', 'minimum_classes', 'minimum_properties', 'minimum_assignments'
        }]) == 0
        pipeline_valid = len(errors) == 0
        governance_valid = len(errors) == 0 and len(warnings) == 0
        return {
            'workbook': str(self.workbook_path),
            'summary': {
                'parser_valid': parser_valid,
                'pipeline_valid': pipeline_valid,
                'governance_valid': governance_valid,
                'errors': len(errors),
                'warnings': len(warnings),
                'normalizations': len(self.normalizations),
            },
            'findings': [asdict(f) for f in self.findings],
            'normalizations': self.normalizations,
        }


def _layman_mapping(code: str) -> dict:
    mapping = {
        'missing_ifc_uri': {
            'title': 'Missing IFC reference',
            'what_it_means': 'This object is missing its official IFC URI reference.',
            'what_to_do': 'Add the correct official IFC URI for this object.',
            'category': 'Object definitions',
        },
        'missing_class_definition': {
            'title': 'Missing object definition',
            'what_it_means': 'This object has no clear description/definition yet.',
            'what_to_do': 'Add a short definition so users understand what the object means.',
            'category': 'Object definitions',
        },
        'unknown_value_list_id': {
            'title': 'Value catalog ID is not registered',
            'what_it_means': 'A property points to a value catalog ID that does not exist in the Wertekatalog tab.',
            'what_to_do': 'Check the Werteliste-ID spelling or register the missing value catalog in Wertekatalog.',
            'category': 'Value catalog issues',
        },
        'noncanonical_value_list_id': {
            'title': 'Value catalog ID does not follow the standard format',
            'what_it_means': 'The value catalog ID exists but is not written in the canonical format expected by the standard.',
            'what_to_do': 'Rename the Werteliste-ID to the canonical generated form shown by the validator.',
            'category': 'Value catalog issues',
        },
        'missing_ifc_property_uri_reference': {
            'title': 'Official IFC property URI missing',
            'what_it_means': 'This property has no official IFC property URI reference.',
            'what_to_do': 'If an official IFC property URI exists, add it. If none exists, you may leave it empty.',
            'category': 'Property definitions',
        },
        'missing_ifc_property_set_reference': {
            'title': 'Official IFC property-set reference missing',
            'what_it_means': 'This property has no official IfcPropertySet or IfcQuantitySet reference.',
            'what_to_do': 'Add the official IFC set reference if applicable; otherwise provide a Merkmalsgruppe.',
            'category': 'Property definitions',
        },
        'missing_property_set_locator': {
            'title': 'No property grouping provided',
            'what_it_means': 'This property has neither an official IFC property-set reference nor a local Merkmalsgruppe.',
            'what_to_do': 'Provide an IfcPropertySet / IfcQuantitySet reference or add a Merkmalsgruppe.',
            'category': 'Property definitions',
        },
        'unknown_property_set_reference': {
            'title': 'Property set reference is unknown',
            'what_it_means': 'The PropertySet used in the template is not registered in the property catalog.',
            'what_to_do': 'Use a registered IfcPropertySet, IfcQuantitySet, or Merkmalsgruppe value.',
            'category': 'Data template assignment issues',
        },
        'matrix_unknown_merkmal_id': {
            'title': 'Property ID in template area is unknown',
            'what_it_means': 'The Data Template references a Merkmal-ID that is not registered in the property tab.',
            'what_to_do': 'Use a Merkmal-ID that exists in Merkmale_Merkmalsgruppen.',
            'category': 'Data template assignment issues',
        },
        'invalid_allowed_values_override': {
            'title': 'Selected values do not match the allowed values',
            'what_it_means': 'The values selected for an object/property combination are not part of the official allowed values of that property.',
            'what_to_do': 'Correct the values or extend the official value catalog if the missing values are truly needed.',
            'category': 'Data template assignment issues',
        },
        'missing_source_code': {
            'title': 'Source code is missing',
            'what_it_means': 'The source/provenance field is empty.',
            'what_to_do': 'Provide a registered source code or use Organisation if no external source exists.',
            'category': 'Document and source governance',
        },
        'unknown_source_code': {
            'title': 'Source code is not registered',
            'what_it_means': 'A source was used that is not formally registered in the document/source register.',
            'what_to_do': 'Register the source in Dokumente_Dokumentgruppen or use Organisation.',
            'category': 'Document and source governance',
        },
        'missing_document_code': {
            'title': 'Document code is missing',
            'what_it_means': 'The canonical document identifier is missing.',
            'what_to_do': 'Provide the canonical document code according to your governance rule.',
            'category': 'Document and source governance',
        },
        'duplicate_document_code': {
            'title': 'Document code is used more than once',
            'what_it_means': 'The same canonical document code appears multiple times.',
            'what_to_do': 'Ensure every document code is unique.',
            'category': 'Document and source governance',
        },
        'missing_ifc_type_object_entity': {
            'title': 'IFC type mapping is missing',
            'what_it_means': 'An IFC object-level mapping exists, but no type-level mapping was provided.',
            'what_to_do': 'Add the IFC type mapping if applicable; otherwise this can often be left as-is.',
            'category': 'Object definitions',
        },
        'missing_predefined_type': {
            'title': 'IFC predefined type is missing',
            'what_it_means': 'No predefined type was provided for this object.',
            'what_to_do': 'Add the predefined type if the IFC mapping requires one.',
            'category': 'Object definitions',
        },
    }
    return mapping.get(code, {
        'title': code.replace('_', ' ').capitalize(),
        'what_it_means': 'The validator found an issue that should be reviewed.',
        'what_to_do': 'Open the referenced sheet and row, review the value, and correct it according to the workbook guidance.',
        'category': 'Other validation issues',
    })


def render_markdown_report(report: dict) -> str:
    summary = report.get('summary', {})
    findings = report.get('findings', [])
    normalizations = report.get('normalizations', [])
    from collections import defaultdict
    grouped = defaultdict(list)
    for f in findings:
        meta = _layman_mapping(f['code'])
        grouped[meta['category']].append((f, meta))

    lines = []
    lines.append('# Data Dictionary Validation Report')
    lines.append('')
    lines.append(f'**Workbook:** `{report.get("workbook")}`')
    lines.append('')
    lines.append('## Overall result')
    lines.append('')
    lines.append(f'- Blocking errors: **{summary.get("errors", 0)}**')
    lines.append(f'- Warnings: **{summary.get("warnings", 0)}**')
    lines.append(f'- Normalizations / derived suggestions: **{summary.get("normalizations", 0)}**')
    lines.append(f'- Pipeline valid: **{summary.get("pipeline_valid", False)}**')
    lines.append('')
    if summary.get('errors', 0) > 0:
        lines.append('> The workbook is **not ready for a clean pass yet**. Please review the blocking errors first.')
    else:
        lines.append('> No blocking validation errors were found. Please still review warnings and normalization notes.')
    lines.append('')
    lines.append('## Findings by topic')
    lines.append('')
    for category in sorted(grouped.keys()):
        lines.append(f'### {category}')
        lines.append('')
        for f, meta in grouped[category]:
            where = []
            if f.get('sheet'):
                where.append(f"Sheet: `{f['sheet']}`")
            if f.get('row'):
                where.append(f"Row: `{f['row']}`")
            if f.get('cell'):
                where.append(f"Cell: `{f['cell']}`")
            lines.append(f"- **{meta['title']}** ({f['level'].upper()})")
            if where:
                lines.append(f"  - Where: {', '.join(where)}")
            lines.append(f"  - What it means: {meta['what_it_means']}")
            lines.append(f"  - What to do: {meta['what_to_do']}")
            lines.append(f"  - Technical detail: `{f['code']}` — {f['message']}")
            lines.append('')
    lines.append('## Normalization notes')
    lines.append('')
    if not normalizations:
        lines.append('- No automatic normalizations or derivation suggestions were recorded.')
    else:
        for n in normalizations:
            where = []
            if n.get('sheet'):
                where.append(f"Sheet: `{n['sheet']}`")
            if n.get('row'):
                where.append(f"Row: `{n['row']}`")
            if n.get('column'):
                where.append(f"Field: `{n['column']}`")
            lines.append(f"- {'; '.join(where)}")
            lines.append(f"  - Original: `{n.get('original_value')}`")
            lines.append(f"  - Normalized / derived: `{n.get('normalized_value')}`")
            lines.append(f"  - Reason: {n.get('reason')}")
            lines.append('')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate HE-DD Strukturvorlage workbook for SchemaForge pipeline use.')
    parser.add_argument('workbook', help='Path to workbook (.xlsx)')
    parser.add_argument('--json-out', help='Optional path to write JSON report')
    parser.add_argument('--md-out', help='Optional path to write layman-readable Markdown report')
    args = parser.parse_args(argv)

    workbook = Path(args.workbook).resolve()
    validator = Validator(workbook)
    report = validator.validate()

    if args.json_out:
        out = Path(args.json_out)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    if args.md_out:
        md_out = Path(args.md_out)
        md_out.write_text(render_markdown_report(report))

    print(json.dumps(report['summary'], indent=2))
    for f in report['findings'][:50]:
        loc = []
        if f['sheet']:
            loc.append(f['sheet'])
        if f['row']:
            loc.append(f"row {f['row']}")
        where = ' @ '.join(loc)
        print(f"[{f['level'].upper()}] {f['code']}: {f['message']}" + (f" ({where})" if where else ''))
    return 1 if not report['summary']['pipeline_valid'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
