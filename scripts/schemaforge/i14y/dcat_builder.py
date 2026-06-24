"""
SchemaForge i14y Pipeline — dcat_builder.py
============================================
Transforms DictionaryMetadata into a DCAT-AP CH compliant JSON payload
ready for the i14y Partner API.

Mapping reference: I14Y handbook — Eingabefelder Datensatz
API endpoint: POST /partner/v1/datasets  (create)
              PUT  /partner/v1/datasets/{identifier}  (update)

Design:
- All field names follow the i14y Partner API schema
  (observed from the existing Dataset JSON and the handbook field table).
- Language codes use BCP-47 / ISO 639: "de", "fr", "it", "en"
- Publisher is resolved by identifier string ("CH_KBOB") — must match
  exactly what is registered on i14y.
- Distributions are generated from the technical endpoints in the metadata.
- conformsTo is a list of URI strings.

Note on i14y identifier:
- We use the DictionaryCode from the Excel (e.g. "dd-kbob") plus version
  as the stable identifier: "KBOB_DD_FM" (human-readable, no umlauts/spaces).
- After first publication the identifier MUST NOT change.
  The version field is updated on each new version instead.
"""

import datetime
from typing import Optional
from .metadata_reader import DictionaryMetadata


# ── i14y Publisher identifier for KBOB ────────────────────────────────────────
# Must match the publisher registered on i14y exactly.
KBOB_PUBLISHER_ID = "615246c9-31e2-42af-b14a-c20c8e23ec6a"

# ── Stable i14y identifier for this dataset ───────────────────────────────────
# Set once, never change after first publication.
I14Y_IDENTIFIER = "KBOB_DD_FM"

# ── i14y theme code for "Construction / Bauen" ───────────────────────────────
I14Y_THEME_CODE = "102"

# ── Access rights: public ─────────────────────────────────────────────────────
ACCESS_RIGHTS_PUBLIC = {
    "code": "PUBLIC",
    "name": {
        "de": "Öffentlich",
        "en": "Public",
        "fr": "Public",
        "it": "Pubblico",
    },
    "uri": "http://publications.europa.eu/resource/authority/access-right/PUBLIC",
}

# ── Confidentiality: no personal data ────────────────────────────────────────
CONFIDENTIALITY_NO_PERSON = {
    "code": "no_person",
    "name": {
        "de": "Enthält keine Personendaten",
        "en": "Does not contain personal data",
        "fr": "Ne contient pas de données personnelles",
        "it": "Non contiene dati personali",
    },
}

# ── Lifecycle → i14y registrationStatus mapping ──────────────────────────────
LIFECYCLE_TO_STATUS = {
    "Preview":    "Candidate",
    "Active":     "Recorded",
    "Deprecated": "Superseded",
    "Retired":    "Retired",
}

# ── License URI mapping ───────────────────────────────────────────────────────
LICENSE_MAP = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC0":        "https://creativecommons.org/publicdomain/zero/1.0/",
    "OGL":        "https://www.nationalarchives.gov.uk/doc/open-government-licence/",
}


def _lang_literal(value: Optional[str], lang: str) -> Optional[dict]:
    if not value:
        return None
    return {"value": value, "language": lang}


def _build_titles(meta: DictionaryMetadata) -> dict:
    titles = {}
    if meta.title_de:
        titles["de"] = meta.title_de
    if meta.title_fr:
        titles["fr"] = meta.title_fr
    if meta.title_en:
        titles["en"] = meta.title_en
    return titles


def _build_descriptions(meta: DictionaryMetadata) -> dict:
    desc = {}
    if meta.description_de:
        desc["de"] = meta.description_de
    if meta.description_fr:
        desc["fr"] = meta.description_fr
    if meta.description_en:
        desc["en"] = meta.description_en
    # Fallback: minimal placeholder if nothing filled
    if not desc:
        desc["de"] = (
            f"{meta.title_de} — Data Dictionary entry (Beschreibung ausstehend)."
        )
    return desc


def _build_contact_points(meta: DictionaryMetadata) -> list:
    if not meta.contact_email:
        return []
    return [
        {
            "kind": "Organization",
            "hasEmail": meta.contact_email,
        }
    ]


def _build_distributions(meta: DictionaryMetadata) -> list:
    """
    Build distribution objects for:
    1. TriG/TTL download (if TTL_Download_URL is set)
    2. SPARQL endpoint (if SPARQL_Endpoint is set)
    3. JSON download (if JSON_Download_URL is set)
    """
    distributions = []
    today = datetime.date.today().isoformat()

    if meta.ttl_download_url:
        distributions.append({
            "title": {
                "de": "RDF/TriG Download — KBOB Data Dictionary FM",
                "en": "RDF/TriG Download — KBOB FM Data Dictionary",
            },
            "description": {
                "de": (
                    "RDF-Datei (TriG-Format) des KBOB Data Dictionary FM. "
                    "Enthält alle Klassen, Eigenschaften und Wertelisten "
                    "im semantischen Datenmodell HE-SEM."
                ),
                "en": (
                    "RDF file (TriG format) of the KBOB FM Data Dictionary. "
                    "Contains all classes, properties and value lists "
                    "in the HE-SEM semantic data model."
                ),
            },
            "accessURL": meta.ttl_download_url,
            "downloadURL": meta.ttl_download_url,
            "format": "application/trig",
            "mediaType": "application/trig",
            "issued": today,
            "modified": today,
            "availability": "http://publications.europa.eu/resource/authority/planned-availability/EXPERIMENTAL",
        })

    if meta.sparql_endpoint:
        distributions.append({
            "title": {
                "de": "SPARQL-Endpunkt — KBOB Data Dictionary FM",
                "en": "SPARQL Endpoint — KBOB FM Data Dictionary",
            },
            "description": {
                "de": (
                    "SPARQL-Endpunkt für semantische Abfragen des KBOB Data Dictionary FM. "
                    "Prototyp-Instanz (GraphDB PoC) — wird künftig auf LINDAS migriert."
                ),
                "en": (
                    "SPARQL endpoint for semantic queries against the KBOB FM Data Dictionary. "
                    "Prototype instance (GraphDB PoC) — to be migrated to LINDAS."
                ),
            },
            "accessURL": meta.sparql_endpoint,
            "format": "application/sparql-results+json",
            "issued": today,
            "modified": today,
            "availability": "http://publications.europa.eu/resource/authority/planned-availability/EXPERIMENTAL",
        })

    if meta.json_download_url:
        distributions.append({
            "title": {
                "de": "JSON-LD Download — KBOB Data Dictionary FM",
                "en": "JSON-LD Download — KBOB FM Data Dictionary",
            },
            "description": {
                "de": "JSON-LD Export des KBOB Data Dictionary FM.",
                "en": "JSON-LD export of the KBOB FM Data Dictionary.",
            },
            "accessURL": meta.json_download_url,
            "downloadURL": meta.json_download_url,
            "format": "application/ld+json",
            "mediaType": "application/ld+json",
            "issued": today,
            "modified": today,
            "availability": "http://publications.europa.eu/resource/authority/planned-availability/EXPERIMENTAL",
        })

    return distributions


def _build_conforms_to(meta: DictionaryMetadata) -> list:
    return [{"uri": uri} for uri in meta.conforms_to if uri]


def _build_keywords(meta: DictionaryMetadata) -> list:
    out = []
    for kw in meta.keywords_de:
        out.append({"label": {"de": kw}})
    for kw in meta.keywords_fr:
        out.append({"label": {"fr": kw}})
    for kw in meta.keywords_en:
        out.append({"label": {"en": kw}})
    return out


def _build_themes(meta: DictionaryMetadata) -> list:
    return [{"code": I14Y_THEME_CODE, "name": {
        "de": "Bauen",
        "en": "Construction",
        "fr": "Construction",
        "it": "Costruzione",
    }}]


def _build_landing_pages(meta: DictionaryMetadata) -> list:
    if meta.more_info_url:
        return [{"uri": meta.more_info_url}]
    return []


def _build_documentation(meta: DictionaryMetadata) -> list:
    return [{"uri": url} for url in meta.documentation_urls if url]


def _build_related(meta: DictionaryMetadata) -> list:
    return [{"uri": url} for url in meta.related_resource_urls if url]


def _build_applicable_legislation(meta: DictionaryMetadata) -> list:
    return [{"uri": url} for url in meta.applicable_legislation_uris if url]


def build_dataset_payload(
    meta: DictionaryMetadata,
    publication_level: str = "Internal",
) -> dict:
    """
    Build the full i14y Partner API JSON payload for a dataset.

    Args:
        meta:              DictionaryMetadata from metadata_reader.
        publication_level: "Internal" (default, safe) or "Public".
                           Start with "Internal" for review, then
                           manually promote to "Public" via UI or API.

    Returns:
        dict ready for JSON serialisation and POST/PUT to i14y Partner API.
    """
    registration_status = LIFECYCLE_TO_STATUS.get(
        meta.lifecycle_status, "Candidate"
    )

    payload = {
        # ── Core DCAT-AP CH fields ─────────────────────────────────────────
        "identifier": I14Y_IDENTIFIER,
        "title": _build_titles(meta),
        "description": _build_descriptions(meta),
        "version": meta.version,

        # ── Publisher ─────────────────────────────────────────────────────
        "publisher": {
            "id": KBOB_PUBLISHER_ID,
            "identifier": "CH_KBOB",
        },

        # ── Access & confidentiality ───────────────────────────────────────
        "accessRights": ACCESS_RIGHTS_PUBLIC,
        "confidentialityPerson": CONFIDENTIALITY_NO_PERSON,
        "publicationLevel": publication_level,
        "registrationStatus": registration_status,

        # ── Contact ───────────────────────────────────────────────────────
        "contactPoints": _build_contact_points(meta),

        # ── Dates ─────────────────────────────────────────────────────────
        "issued":    meta.release_date or datetime.date.today().isoformat(),
        "modified":  datetime.date.today().isoformat(),

        # ── Language ──────────────────────────────────────────────────────
        "languages": meta.metadata_languages or [meta.primary_language.split('-')[0]],

        # ── Themes & keywords ─────────────────────────────────────────────
        "themes": _build_themes(meta),
        "keywords": _build_keywords(meta),

        # ── Spatial coverage ──────────────────────────────────────────────
        "spatial": ([{"uri": uri} for uri in meta.spatial_coverage] if meta.spatial_coverage else [
            {
                "uri": "https://publications.europa.eu/resource/authority/country/CHE",
                "label": {"de": "Schweiz", "en": "Switzerland",
                          "fr": "Suisse", "it": "Svizzera"},
            }
        ]),

        # ── Landing pages ─────────────────────────────────────────────────
        "landingPages": _build_landing_pages(meta),

        # ── Distributions ─────────────────────────────────────────────────
        "distributions": _build_distributions(meta),

        # ── Standards conformance ─────────────────────────────────────────
        "conformsTo": _build_conforms_to(meta),

        # ── Empty lists (required by schema, filled later) ────────────────
        "documentation":        _build_documentation(meta),
        "isReferencedBy":       [],
        "relations":            _build_related(meta),
        "applicableLegislation": _build_applicable_legislation(meta),
        "qualifiedAttributions": [],
        "qualifiedRelations":   [],
        "images":               [],
        "geoIvIds":             [],
        "temporalCoverage":     [],
        "identifiers":          [I14Y_IDENTIFIER],
    }

    return payload
