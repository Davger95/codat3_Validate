# Data Dictionary Validation Report

**Workbook:** `/home/Dave/.openclaw/workspace-datadict/P_workspace_codat3_validator/templates/Strukturvorlage_DataDictionary_v2_empty.xlsx`

## Gesamtergebnis

- Blockierende Fehler: **4**
- Warnungen: **0**
- Normalisierungen / abgeleitete Hinweise: **0**
- Pipeline gültig: **False**

> Das Workbook ist **noch nicht bereit für einen fehlerfreien Durchlauf**. Bitte prüfen Sie zuerst die blockierenden Fehler.

## Befunde nach Thema

### Other validation issues

- **Missing dictionary field** (ERROR)
  - Ort: Sheet: `Header`, Row: `4`
  - Bedeutung: Der Validator hat ein Problem gefunden, das geprüft werden sollte.
  - Empfohlene Korrektur: Öffnen Sie das referenzierte Sheet und die betroffene Row, prüfen Sie den Wert und korrigieren Sie ihn gemäss der Workbook-Guidance.
  - Technisches Detail: `missing_dictionary_field` — Missing required Header value: OrganizationCode. Use a short lowercase code, max 7 characters.

- **Missing dictionary field** (ERROR)
  - Ort: Sheet: `Header`, Row: `8`
  - Bedeutung: Der Validator hat ein Problem gefunden, das geprüft werden sollte.
  - Empfohlene Korrektur: Öffnen Sie das referenzierte Sheet und die betroffene Row, prüfen Sie den Wert und korrigieren Sie ihn gemäss der Workbook-Guidance.
  - Technisches Detail: `missing_dictionary_field` — Missing required Header value: DictionaryName (EN). Also fill at least one local DictionaryName in DE, FR, or IT.

- **Missing dictionary field** (ERROR)
  - Ort: Sheet: `Header`, Row: `9`
  - Bedeutung: Der Validator hat ein Problem gefunden, das geprüft werden sollte.
  - Empfohlene Korrektur: Öffnen Sie das referenzierte Sheet und die betroffene Row, prüfen Sie den Wert und korrigieren Sie ihn gemäss der Workbook-Guidance.
  - Technisches Detail: `missing_dictionary_field` — Missing required Header value: DictionaryVersion. Use semantic versioning like 1.0.0.

- **Missing dictionary field** (ERROR)
  - Ort: Sheet: `Header`, Row: `13`
  - Bedeutung: Der Validator hat ein Problem gefunden, das geprüft werden sollte.
  - Empfohlene Korrektur: Öffnen Sie das referenzierte Sheet und die betroffene Row, prüfen Sie den Wert und korrigieren Sie ihn gemäss der Workbook-Guidance.
  - Technisches Detail: `missing_dictionary_field` — Missing required Header value: LifecycleStatus. Choose one of the allowed status values.

## Normalisierungshinweise

- Es wurden keine automatischen Normalisierungen oder Ableitungshinweise erfasst.
