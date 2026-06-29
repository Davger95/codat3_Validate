# Data Dictionary Validierungs-MVP

Dieses Repository stellt eine Excel-Vorlage und eine GitHub-basierte Validierung für Data Dictionaries bereit.

## Kanonische Vorlage

- `templates/Strukturvorlage_DataDictionary_empty.xlsx`

Diese leere Vorlage ist der Startpunkt für Nutzerinnen und Nutzer.

## Typischer Nutzer-Workflow

1. Vorlage herunterladen
2. Eigene Data-Dictionary-Inhalte eintragen
3. Datei in einen GitHub-Branch hochladen oder committen
4. GitHub Action **Validate Data Dictionary** starten
5. Validierungsbericht als Artefakt und in der Job-Zusammenfassung prüfen

## Wichtiger Hinweis

Die leere Vorlage ist absichtlich noch **nicht vollständig ausgefüllt**. Wenn sie unverändert validiert wird, sind Fehler für fehlende Mindestangaben – insbesondere in `Dictionary_core` – korrekt und gewünscht.

## Ausserhalb des aktuellen MVP

Nicht Teil dieses öffentlichen MVP sind derzeit:

- RDF-Erzeugung
- bSDD-Publikation
- i14y-Publikation
- LINDAS-Publikation
- sonstige Export-/Publishing-Pipelines
