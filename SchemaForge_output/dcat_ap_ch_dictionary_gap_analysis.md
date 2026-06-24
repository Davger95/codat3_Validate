# DCAT-AP-CH Dictionary Tab Gap Analysis

## Normative source anchors
- `sources/Standards/STAN_e_REP_2025-07-11_eCH-0200_V3.0.0_DCAT Application Profile for Data Portals in Switzerland (DCAT-AP CH) v3.pdf`
- `sources/i14y/Dataset_df40311c-eb37-4186-a6da-21ebaca5110a.Json`
- `scripts/schemaforge/i14y/metadata_reader.py`
- `scripts/schemaforge/i14y/dcat_builder.py`

## Current Dictionary tab fields
- OrganizationCode
- DictionaryCode
- DictionaryName (DE)
- DictionaryName (FR)
- DictionaryName (EN)
- DictionaryVersion
- DictionaryUri

## Current pipeline-supported fields outside the visible sample tab structure
Already expected by `metadata_reader.py` but not present in the sample workbook structure:
- Owner / Publisher
- ContactEmail
- LifecycleStatus
- ReleaseDate
- QualityAssuranceProcedure
- QualityAssuranceProcedureUrl
- License
- LicenseUrl
- PrimaryLanguage
- eCH_Theme
- SPARQL_Endpoint
- TTL_Download_URL
- JSON_Download_URL
- MoreInfoUrl
- ConformsTo_ISO23386
- ConformsTo_ISO12006_3
- ConformsTo_DCAT_AP_CH
- Description (DE)
- Description (FR)
- Description (EN)

## DCAT-AP-CH / i14y relevant dataset metadata to support in Dictionary tab
### Mandatory or operationally mandatory for the current pipeline
- DictionaryCode / stable identifier → `dct:identifier`
- DictionaryName (DE/FR/EN) → `dct:title`
- Description (DE/FR/EN) → `dct:description`
- Owner / Publisher → `dct:publisher`
- ContactEmail → `dcat:contactPoint`
- DictionaryVersion → `dcat:version`
- DictionaryUri → canonical dataset URI / identifier basis
- LifecycleStatus → mapped to i14y registration status

### Recommended / important for DCAT-AP-CH dataset metadata
- ReleaseDate → `dct:issued`
- ModifiedDate → `dct:modified`
- Keyword(s) multilingual or at least DE → `dcat:keyword`
- LandingPage / MoreInfoUrl → `dcat:landingPage`
- PrimaryLanguage / MetadataLanguages → `dct:language`
- Theme (EU / eCH / i14y theme mapping) → `dcat:theme`
- AccessRights → `dct:accessRights`
- License / LicenseUrl → `dct:license`
- SpatialCoverage → `dct:spatial`
- TemporalCoverage → `dct:temporal`
- ConformsTo_* / additional ConformsTo URIs → `dct:conformsTo`
- DocumentationUrl(s) → `foaf:page`
- RelatedResource / LegalBasis / ApplicableLegislation → `dct:relation` or `dcatap:applicableLegislation`
- VersionNotes → `adms:versionNotes`
- Qualified attribution / creator / provenance fields if modeled later

## Observed mismatch
The sample workbook note in `Dictionary!D11` says `LifecycleStatus` is required, but the field is not present as a formal row in column A. That inconsistency should be fixed by adding explicit field rows, not by weakening the metadata model.

## Implementation direction
1. Extend the Dictionary tab template with explicit DCAT/i14y-relevant field rows.
2. Extend `validate_strukturvorlage.py` to validate the extended Dictionary fields with appropriate requirement levels.
3. Extend `metadata_reader.py` to read the richer field set as first-class inputs rather than relying on defaults/hardcoding.
4. Extend `dcat_builder.py` to map the richer metadata into payload fields with fewer hardcoded constants.
5. Keep guidance rows, but ensure every validator-required field is also a real `Field` row.
