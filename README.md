# Data Dictionary Validierungs-MVP

Dieses Repository stellt eine **Excel-Vorlage** und eine **GitHub-basierte Validierung** für strukturierte Data Dictionaries bereit.

## Was ist dieses Repository?

Dieses Repository enthält den aktuellen **Validierungs-MVP** für den aligned Data-Dictionary-Workflow.

Damit können Nutzerinnen und Nutzer:

1. die leere kanonische Excel-Vorlage herunterladen,
2. ihre eigenen Inhalte in die Vorlage eintragen,
3. die ausgefüllte Arbeitsmappe in einen GitHub-Branch hochladen oder committen,
4. die GitHub-Validierung starten,
5. Validierungsberichte mit Fehlern, Warnungen und Hinweisen herunterladen.

## Wofür ist die Excel-Vorlage gedacht?

Die Vorlage dient dazu, ein Data Dictionary strukturiert zu erfassen, insbesondere in den Tabellen:

- `Objekte`
- `Merkmale`
- `Werte`
- `Dokumente`
- `Merkmalgruppen`
- `Dictionary_core`
- `Dictionary_public`
- `Data_Template`

Die leere Vorlage ist der **Startpunkt** für Nutzer. Die GitHub-Validierung prüft sowohl die kanonische leere Vorlage als Smoke Test als auch ausgefüllte Arbeitsmappen, die Nutzer selbst bereitstellen.

## Wo finde ich die Vorlage?

Kanonische Vorlage:

- `templates/Strukturvorlage Datenkataloge_Abgeglichen_v2__empty.xlsx`

## Wie fülle ich die Vorlage aus?

1. Lade die kanonische Vorlage herunter.
2. Trage deine Inhalte in die vorgesehenen Tabellen und Spalten ein.
3. Behalte die Blattnamen, Spaltennamen und Hinweiszeilen unverändert bei.
4. Nutze Dropdowns und vorgegebene Werte dort, wo sie vorhanden sind.
5. Speichere die ausgefüllte Datei als `.xlsx`.

## Wie validiere ich eine ausgefüllte Arbeitsmappe über GitHub?

Wenn GitHub Actions für das Repository aktiviert sind, ist der empfohlene Ablauf:

1. Lege einen Branch an oder nutze einen bestehenden Branch.
2. Lade deine ausgefüllte `.xlsx`-Datei in das Repository hoch oder committe sie in den Branch.
3. Öffne den GitHub-Actions-Workflow **Validate Data Dictionary**.
4. Trage bei Bedarf den Pfad zur Arbeitsmappe ein (`workbook_path`).
5. Starte den Workflow.

Der Standardpfad ist:

- `templates/Strukturvorlage Datenkataloge_Abgeglichen_v2__empty.xlsx`

Für eigene Arbeitsmappen gibst du stattdessen den relativen Pfad zu deiner Datei an.

## Wo finde ich den Validierungsbericht?

Nach dem Workflow-Lauf findest du:

- den Markdown-Bericht in der Job-Zusammenfassung,
- die JSON/Markdown/Summary-Dateien als GitHub-Artefakte,
- lokal im Repository unter `SchemaForge_output/`, wenn du die Validierung lokal ausführst.

## Was bedeuten Fehler, Warnungen und Normalisierungshinweise?

- **Fehler**: müssen behoben werden; die Datei ist in diesem Zustand nicht gültig.
- **Warnungen**: sollten überprüft werden; oft sind Inhalte unvollständig, zweifelhaft oder nur teilweise konsistent.
- **Normalisierungshinweise**: zeigen automatische Interpretation, Ableitung oder Standardisierung an.

## Was ist aktuell bewusst nicht enthalten?

Dieser öffentliche MVP umfasst **nur die Validierung**.

Bewusst **nicht** enthalten bzw. noch nicht freigegeben sind:

- RDF-Erzeugung
- bSDD-Publikation
- i14y-Publikation
- LINDAS-Publikation
- sonstige Export-/Publishing-Pipelines

Diese Teile werden erst später wieder eingeführt, sobald sie repariert, getestet und separat verifiziert sind.

## Lokale Ausführung

```bash
python3 scripts/schemaforge/run_github_validation.py \
  --workspace /home/Dave/.openclaw/workspace-datadict \
  --workbook-path "templates/Strukturvorlage Datenkataloge_Abgeglichen_v2__empty.xlsx"
```

Weitere Details:

- `docs/github-validation-wrapper.md`
- `docs/validierungslogik.md`
