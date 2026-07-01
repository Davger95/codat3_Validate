# GettingStarted

Diese Anleitung hilft Ihnen Schritt für Schritt beim Einstieg in das öffentliche Repository.

## 1. Zugriff anfragen

Bevor Sie mit dem Repository arbeiten, fordern Sie bitte Zugriff an.

Senden Sie dazu eine E-Mail an:

**repo-access@example.org**

> Hinweis: Diese Adresse ist aktuell ein Platzhalter und kann später durch die echte Kontaktadresse ersetzt werden.

## 2. Repository öffnen oder klonen

Sobald Sie Zugriff haben, öffnen oder klonen Sie das Repository lokal.

Beispiel:

```bash
git clone <REPOSITORY-URL>
cd codat3_Validate
```

## 3. Repository-Struktur verstehen

Die wichtigsten Bereiche sind:

- `README.md`  
  Einstieg und Überblick
- `GettingStarted.md`  
  diese Onboarding-Anleitung
- `docs/validierungslogik.md`  
  fachliche Erklärung der Validierungslogik
- `docs/validierung-mit-github-actions.md`  
  Erklärung des GitHub-Validierungsablaufs
- `templates/Strukturvorlage_DataDictionary_v2_empty.xlsx`  
  kanonische leere Vorlage
- `templates/test_files/Strukturvorlage_DataDictionary_v5_AreaMgmt.xlsx`  
  ausgefülltes Beispiel
- `scripts/validator/run_github_validation.py`  
  GitHub-kompatibler Einstiegspunkt für die Validierung
- `scripts/validator/validate_strukturvorlage.py`  
  zentrale Validierungslogik

## 4. Leere Vorlage herunterladen

Verwenden Sie für neue Arbeiten immer diese Datei:

- `templates/Strukturvorlage_DataDictionary_v2_empty.xlsx`

Diese Datei ist die öffentliche Startvorlage.

## 5. Beispiel-Datei anschauen

Wenn Sie zuerst verstehen möchten, wie eine ausgefüllte Datei aussieht, öffnen Sie:

- `templates/test_files/Strukturvorlage_DataDictionary_v5_AreaMgmt.xlsx`

Diese Datei dient als öffentliches Beispiel.

## 6. Vorlage ausfüllen

Füllen Sie Ihre eigene Arbeitsmappe auf Basis der leeren Vorlage aus.

Wichtig:

- Blattnamen nicht umbenennen
- Kopfzeilen nicht verschieben
- Strukturblöcke nicht löschen
- Pflichtfelder im `Header` ausfüllen

## 7. Validierung ausführen

Der öffentliche Standardweg ist die GitHub Action.

Grundablauf:

1. Ihre ausgefüllte `.xlsx` in einen Branch hochladen oder committen
2. GitHub Action **Validate Data Dictionary** starten
3. bei Bedarf `workbook_path` auf Ihre Datei setzen
4. Bericht herunterladen und prüfen

## 8. Berichte lesen

Der Validator unterscheidet zwischen:

- **Fehler** = müssen behoben werden
- **Warnungen** = sollen geprüft werden
- **Normalisierungen** = zeigen automatische Ableitungen oder Standardisierungen

## 9. Relevante Dokumentation lesen

Für den Alltag sind diese Dateien besonders wichtig:

- `README.md`
- `docs/validierungslogik.md`
- `docs/validierung-mit-github-actions.md`

## 10. Mit dem Beispiel vergleichen

Wenn Ihre Datei nicht wie erwartet validiert, vergleichen Sie sie mit:

- der leeren Vorlage
- dem ausgefüllten AreaMgmt-Beispiel

So können Strukturfehler meist schnell erkannt werden.
