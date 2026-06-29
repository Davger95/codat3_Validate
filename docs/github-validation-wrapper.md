# GitHub-Validierung

## Zweck

Dieser Workflow validiert Excel-Arbeitsmappen auf Basis des aktuellen aligned Data-Dictionary-MVP.

## Standardfall

Der Standard-Smoke-Test verwendet die kanonische leere Vorlage:

- `templates/Strukturvorlage Datenkataloge_Abgeglichen_v2__empty.xlsx`

## Validierung einer ausgefüllten Arbeitsmappe

Wenn du eine eigene ausgefüllte `.xlsx`-Datei validieren willst:

1. lade oder committe die Datei in einen Branch,
2. öffne GitHub Actions,
3. starte den Workflow **Validate Data Dictionary**,
4. setze `workbook_path` auf den relativen Pfad deiner Datei.

Beispiel:

- `templates/mein-katalog.xlsx`
- `uploads/testlauf.xlsx`

## Verwendeter Befehl

```bash
python3 scripts/schemaforge/run_github_validation.py \
  --workspace /home/Dave/.openclaw/workspace-datadict \
  --workbook-path "templates/Strukturvorlage Datenkataloge_Abgeglichen_v2__empty.xlsx"
```

Der Workflow verwendet denselben Befehl, aber mit dem in GitHub angegebenen `workbook_path`.

## Berichte und Artefakte

Der Workflow erzeugt:

- `SchemaForge_output/github_validation_report.json`
- `SchemaForge_output/github_validation_report.md`
- `SchemaForge_output/github_validation_summary.json`

Diese Berichte werden als GitHub-Artefakte hochgeladen.

Zusätzlich wird der Markdown-Bericht in der Job-Zusammenfassung angezeigt.

## Was tun bei Fehlern?

Wenn die Validierung fehlschlägt:

1. öffne zuerst den Markdown-Bericht,
2. prüfe die Fehler nach Tabellenblatt, Zeile und Feld,
3. korrigiere die Excel-Datei,
4. committe die korrigierte Datei erneut,
5. starte den Workflow nochmals.

## Aktueller Geltungsbereich

Dieser öffentliche MVP deckt die **Validierung** ab:

- leere kanonische Vorlage als Smoke Test,
- ausgefüllte Arbeitsmappen von Nutzerinnen und Nutzern,
- Berichterstellung über Fehler, Warnungen und Normalisierungen.

Bewusst **nicht** enthalten sind derzeit:

- RDF-Erzeugung
- bSDD-Publikation
- i14y-Publikation
- LINDAS-Publikation
- sonstige Export-/Publishing-Pipelines
