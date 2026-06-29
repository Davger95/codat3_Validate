# GitHub-Validierung

## Standardpfad

Die GitHub Action validiert standardmässig:

- `templates/Strukturvorlage_DataDictionary_empty.xlsx`

## Eigene Arbeitsmappe validieren

1. `.xlsx`-Datei in einen Branch hochladen oder committen
2. Workflow **Validate Data Dictionary** starten
3. Optional `workbook_path` auf den relativen Pfad der eigenen Datei setzen
4. Bericht und Artefakte herunterladen

## Aktueller Geltungsbereich

Die öffentliche Branch-Version deckt die Validierung von Data Dictionaries ab.

Export- und Publikationspfade (RDF, bSDD, i14y, LINDAS) sind bewusst nicht Teil dieses MVP.
