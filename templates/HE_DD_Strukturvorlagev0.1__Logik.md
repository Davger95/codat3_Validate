# HE_DD_Strukturvorlage v0.1 — Logik

Diese Datei erklärt in einfacher Sprache, **welche Spalten der Strukturvorlage gegen feste Werte- oder Referenzlisten geprüft werden** und **welche Spalten gegen ein bestimmtes Formatmuster (REGEX-Regel) geprüft werden**.

Wichtig:
- **Spaltennamen, Sheet-Namen und Feldnamen bleiben absichtlich im Original**.
- So bleibt die Rückverfolgbarkeit zur Excel-Datei erhalten.
- Diese Übersicht beschreibt die **aktuell im Validator umgesetzte Logik**.

---

## 1) Spalten mit Prüfung gegen Werte- oder Referenzlisten

Hier prüft der Validator nicht einfach auf „irgendein Text“, sondern gegen eine bekannte Menge von erlaubten Werten oder Referenzen.

### A. `Klassen`

#### `IFC URI`
**Was wird geprüft?**
- Der Wert muss auf einen gültigen buildingSMART / bSDD IFC-Identifier zeigen.
- Der Wert muss in der autoritativen IFC/bSDD-Referenz vorhanden sein.

**Einfach erklärt:**
- Hier darf nicht irgendeine URI eingetragen werden.
- Der Validator prüft, ob die URI wirklich aus dem offiziellen IFC/bSDD-Identifierraum stammt.

**Art der Logik:**
- Referenzliste / autoritative URI-Menge

---

#### `PredefinedType`
**Was wird geprüft?**
- Das Feld ist **optional**.
- Wenn ein Wert eingetragen wird, muss dieser zu einem gültigen IFC `PredefinedType` passen.
- Die Prüfung erfolgt im Zusammenhang mit `IfcObject Entity`.
- Wenn zusätzlich `IFC URI` vorhanden ist, wird auch auf Konsistenz zwischen `IfcObject Entity`, `PredefinedType` und `IFC URI` geprüft.

**Einfach erklärt:**
- Leer ist erlaubt.
- Wenn aber etwas eingetragen wird, muss es ein echter gültiger IFC-PredefinedType sein.

**Art der Logik:**
- Werteliste / autoritative IFC-Referenzlogik

---

#### `Source`
**Was wird geprüft?**
- Der Wert muss ein registrierter `SourceCode` aus `Dokumente_Dokumentgruppen` sein,
  oder `Organisation`.

**Einfach erklärt:**
- Es dürfen nur bekannte/registrierte Quellen verwendet werden.

**Art der Logik:**
- Referenzliste

---

### B. `Merkmale_Merkmalsgruppen`

#### `DataType (Base Type)`
**Was wird geprüft?**
- Nur definierte Grundtypen sind erlaubt.

**Aktuell erlaubte Werte:**
- `STRING`
- `INTEGER`
- `REAL`
- `BOOLEAN`
- `TIME`
- `DATETIME`

**Einfach erklärt:**
- Hier gibt es eine feste kleine Liste von erlaubten Datentypen.

**Art der Logik:**
- Werteliste

---

#### `Werteliste-ID`
**Was wird geprüft?**
- Wenn eine Werteliste referenziert wird, muss die `Werteliste-ID` zu einem registrierten Eintrag passen.
- Zusätzlich prüft der Validator, ob die ID der erwarteten kanonischen Form entspricht.

**Einfach erklärt:**
- Die ID darf nicht frei erfunden sein.
- Sie muss zur offiziellen/registrierten Werteliste passen.

**Art der Logik:**
- Referenzliste + kanonische Namenslogik

---

#### `Werteliste`
**Was wird geprüft?**
- Wenn hier Werte eingetragen werden, behandelt der Validator sie als Liste.
- Er erkennt JSON-ähnliche Listen wie z. B. `["A", "B"]`.
- Er kann auch ältere Trennformate wie Komma/Semikolon einlesen.
- Doppelte Werte werden erkannt.

**Einfach erklärt:**
- Diese Spalte wird nicht als Freitext verstanden, sondern als echte Werteliste.

**Art der Logik:**
- Werteliste

---

#### `IfcPropertySet (Pset)`
#### `IfcQuantitySet (Qto)`
**Was wird geprüft?**
- Wenn hier eine URI eingetragen wird, muss sie aus dem gültigen buildingSMART / bSDD-Identifierraum stammen.
- Wenn eine autoritative Referenz verfügbar ist, wird auch geprüft, ob sie dort wirklich existiert.

**Einfach erklärt:**
- Auch hier sind nicht beliebige URIs erlaubt.

**Art der Logik:**
- Referenzliste / autoritative URI-Menge

---

### C. `KlassenMerkmal`

#### `Merkmal-ID`
**Was wird geprüft?**
- Die `Merkmal-ID` muss in `Merkmale_Merkmalsgruppen` registriert sein.

**Einfach erklärt:**
- In `KlassenMerkmal` darf nur auf Merkmale verwiesen werden, die im Merkmalskatalog wirklich existieren.

**Art der Logik:**
- Referenzliste

---

#### `PropertySet`
**Was wird geprüft?**
- Wenn ein `PropertySet` eingetragen wird, muss es in den registrierten Property-Set-/Merkmalsgruppen-Referenzen vorkommen.

**Einfach erklärt:**
- Es dürfen nur bekannte/registrierte Gruppen oder Sets verwendet werden.

**Art der Logik:**
- Referenzliste

---

#### Objekt-Spalten ab dem Bereich rechts von `Property (EN)`
(z. B. die objektbezogenen Spalten mit `x` oder eingeschränkten Werten)

**Was wird geprüft?**
- `x` bedeutet: das Merkmal ist zugewiesen.
- Wenn statt `x` konkrete Werte eingetragen werden, interpretiert der Validator diese als eingeschränkte Allowed Values.
- Diese Werte müssen exakt zur offiziellen Werteliste des jeweiligen Merkmals passen.

**Einfach erklärt:**
- Sobald in einer Objektspalte konkrete Werte stehen, werden diese gegen die erlaubten Werte des Merkmals geprüft.

**Art der Logik:**
- Werteliste / Allowed Values

---

### D. `Dokumente_Dokumentgruppen`

#### `SourceCode`
**Was wird geprüft?**
- `SourceCode` ist selbst die Referenzbasis für andere Teile der Vorlage.
- Andere Bereiche wie `Klassen.Source` werden dagegen geprüft.

**Einfach erklärt:**
- Dieses Sheet definiert die offizielle Liste der erlaubten Quellen.

**Art der Logik:**
- Referenzregister / Stammliste

---

### E. `Dictionary core` / `Dictionary public`

Diese Tabs enthalten aktuell **weniger klassische Listenlogik**, sondern vor allem Pflichtfelder und Formatprüfungen.

Eine Ausnahme ist:

#### `LifecycleStatus`
**Was wird geprüft?**
- Nur bekannte Statuswerte sind erlaubt.

**Erlaubte Werte:**
- `Preview`
- `Active`
- `Inactive`
- `Deprecated`
- `Retired`
- `Candidate`
- `Recorded`
- `Superseded`
- `Incomplete`

**Art der Logik:**
- Werteliste

---

### F. `ConceptRelation`

#### `ConceptType`
**Was wird geprüft?**
- Nur definierte Concept-Typen sind erlaubt.

**Erlaubte Werte:**
- `Class`
- `Property`
- `AllowedValue`
- `PropertySet`
- `Enumeration`
- `Other`

**Art der Logik:**
- Werteliste

---

#### `RelationType`
**Was wird geprüft?**
- Nur definierte SKOS/OWL-Relationen sind erlaubt.

**Erlaubte Werte:**
- `skos:exactMatch`
- `skos:closeMatch`
- `skos:narrowMatch`
- `skos:broadMatch`
- `skos:relatedMatch`
- `owl:sameAs`

**Art der Logik:**
- Werteliste

---

## 2) Spalten mit REGEX- oder Format-Regeln

Hier geht es nicht um eine Liste von erlaubten Werten, sondern um ein **bestimmtes Muster / Format**, das eingehalten werden muss.

### A. `Dictionary core`

#### `DictionaryVersion`
**Regel:**
- muss dem Muster `MAJOR.MINOR.PATCH` folgen
- Beispiel: `0.1.0`

**Technische Regel:**
- SemVer-Regel
- intern via Regex geprüft

---

#### `DictionaryUri`
**Regel:**
- muss eine gültige absolute URI / IRI sein

**Einfach erklärt:**
- Kein lokaler Text, kein Kürzel, sondern eine vollständige Web-/Identifier-Adresse.

**Technische Regel:**
- Formatprüfung auf absolute URI

---

### B. `Dictionary public`

#### `PrimaryLanguage`
**Regel:**
- muss wie ein Sprachcode aussehen, z. B.
  - `de`
  - `fr`
  - `en`
  - `de-CH`

**Technische Regel:**
- Regex für ISO-/BCP47-ähnliches Sprachformat

---

#### `ReleaseDate`
#### `ModifiedDate`
**Regel:**
- müssen im Format `YYYY-MM-DD` eingetragen werden
- Beispiel: `2026-06-25`

**Technische Regel:**
- Regex für Datumsformat

---

#### `ContactEmail`
**Regel:**
- muss wie eine E-Mail-Adresse aussehen

**Wichtig:**
- die aktuelle Prüfung ist eher einfach
- derzeit wird mindestens geprüft, ob ein `@` vorhanden ist

**Technische Regel:**
- einfache Formatprüfung, noch keine strenge Voll-Regex

---

### C. `Klassen`

#### `IFC URI`
**Regel:**
- muss eine gültige absolute URI sein
- und zusätzlich im richtigen IFC/bSDD-Namespace liegen

**Wichtig:**
- das ist eine Mischung aus:
  - Formatprüfung
  - Namespace-Regel
  - Referenzprüfung

---

### D. `Merkmale_Merkmalsgruppen`

#### `IfcPropertySet (Pset)`
#### `IfcQuantitySet (Qto)`
**Regel:**
- wenn eine URI eingetragen wird, muss sie formal gültig sein
- zusätzlich muss sie im richtigen IFC/bSDD-Namespace liegen

**Wichtig:**
- auch hier ist es eine Kombination aus Format- und Referenzlogik

---

### E. `Dokumente_Dokumentgruppen`

#### `Dokument URI`
**Regel:**
- wenn ein Wert eingetragen wird, muss es eine gültige absolute URI sein

---

### F. `ConceptRelation`

#### `RelatedConceptUri`
**Regel:**
- muss eine gültige absolute URI sein

---

## 3) Kurzfassung für Anwender

Wenn Sie schnell verstehen wollen, **wo der Validator besonders streng ist**, dann gilt:

### Besonders wichtig bei festen Listen / Referenzen
- `Klassen.IFC URI`
- `Klassen.PredefinedType` (wenn befüllt)
- `Klassen.Source`
- `Merkmale_Merkmalsgruppen.DataType (Base Type)`
- `Merkmale_Merkmalsgruppen.Werteliste-ID`
- `Merkmale_Merkmalsgruppen.Werteliste`
- `Merkmale_Merkmalsgruppen.IfcPropertySet (Pset)`
- `Merkmale_Merkmalsgruppen.IfcQuantitySet (Qto)`
- `KlassenMerkmal.Merkmal-ID`
- `KlassenMerkmal.PropertySet`
- `KlassenMerkmal` Objektspalten mit eingeschränkten Werten
- `Dictionary core.LifecycleStatus`
- `ConceptRelation.ConceptType`
- `ConceptRelation.RelationType`

### Besonders wichtig bei Format-/Regex-Regeln
- `Dictionary core.DictionaryVersion`
- `Dictionary core.DictionaryUri`
- `Dictionary public.PrimaryLanguage`
- `Dictionary public.ReleaseDate`
- `Dictionary public.ModifiedDate`
- `Dictionary public.ContactEmail`
- alle URI-Spalten mit externer Referenzfunktion

---

## 4) Praktische Lesart

Eine gute Faustregel ist:

- **Wenn eine Spalte auf etwas Offizielles verweist**, prüft der Validator meistens gegen eine Liste oder Referenzmenge.
- **Wenn eine Spalte wie ein technisches Format aussieht** (Version, URI, Sprachcode, Datum), prüft der Validator meistens gegen ein Muster.

---

## 5) Hinweis zum Umfang

Diese Datei beschreibt die **derzeit umgesetzte Logik im Validator**.
Sie beschreibt **nicht automatisch jede gewünschte zukünftige Regel**, sondern den aktuellen Stand der implementierten Prüfung.
