# Data Dictionary Validierungs-MVP

Dieses Repository stellt die **öffentliche Excel-Vorlage** und die **GitHub-basierte Validierung** für ausgefüllte Data Dictionaries bereit.

## Kanonische Vorlage

- `templates/Strukturvorlage_DataDictionary_v2_empty.xlsx`

Diese Datei ist die einzige kanonische öffentliche Vorlage.

## Öffentlicher Nutzer-Workflow

1. Vorlage herunterladen
2. Vorlage ausfüllen
3. Ausgefüllte `.xlsx` in das Repository hochladen oder committen
4. GitHub Action **Validate Data Dictionary** manuell starten und bei Bedarf `workbook_path` auf die eigene Datei setzen
5. Validierungsbericht als Artefakt herunterladen und lesen

## Öffentliche Blattnamen der Vorlage

Die Vorlage arbeitet im MVP mit diesen öffentlichen Blattnamen:

- `Header`
- `Classes`
- `Properties`
- `Values`
- `Documents`
- `GroupOfProperties`
- `Rules`
- `Data_Template`

## Wichtiger Hinweis zum MVP

Der öffentliche MVP ist auf die **Validierung von ausgefüllten Arbeitsmappen** ausgelegt.

- Die Validierung einer ausgefüllten Arbeitsmappe ist der eigentliche Nutzer-Workflow.
- Die Validierung der leeren Vorlage ist nur der **Standard-Smoke-Test** der GitHub Action.

## Ausserhalb des aktuellen öffentlichen MVP

Nicht Teil dieses öffentlichen MVP sind derzeit:

- RDF-Erzeugung
- bSDD-Publikation
- i14y-Publikation
- LINDAS-Publikation
- sonstige Export-/Publishing-Pipelines
