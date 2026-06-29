# Validierungslogik

Diese Datei erklärt in einfacher Sprache, was der Validator prüft.

## A. Struktur der Vorlage

Der Validator prüft zuerst die Struktur der Arbeitsmappe.

Dazu gehört insbesondere:

- die erforderlichen Tabellenblätter müssen vorhanden sein,
- die Blattnamen dürfen nicht umbenannt werden,
- wichtige Spaltennamen dürfen nicht verändert werden,
- Hinweiszeilen und Kopfzeilen dürfen nicht gelöscht oder verschoben werden,
- die Datei muss technisch lesbar bleiben.

Wenn die Struktur nicht stimmt, kann der Validator die Datei nicht zuverlässig interpretieren.

## B. Pflichtfelder

Bestimmte Felder sind Pflichtfelder.

Wenn Pflichtangaben fehlen, meldet der Validator Fehler. Beispiele:

- Pflichtwerte in `Dictionary_core`
- Pflichtangaben in `Objekte`, `Merkmale`, `Dokumente` oder `Merkmalgruppen`
- fehlende Referenzen in `Data_Template`

Die Fehlermeldung zeigt an, welche Zelle oder welche Zeile ergänzt werden muss.

## C. Datentypen

Der Validator prüft, ob Werte zum erwarteten Typ passen.

Beispiele:

- Text
- Zahl
- Boolean
- Datum
- URI
- kontrollierte Werte aus Dropdowns

Datumsfelder müssen z. B. im erwarteten Format stehen. URI-Felder müssen wie gültige Adressen aussehen.

## D. Dropdowns / erlaubte Werte

Viele Spalten haben erlaubte Werte oder Dropdown-Listen.

Dann gilt:

- nur diese Werte sind erlaubt,
- freie Texteingaben können fehlschlagen,
- die Werte müssen zur jeweiligen `Dropdownregeln`-Liste passen.

Beispiele:

- `Objekte.Objekt-Einordnung`
- `Status`
- `Dokumente.Sicherheitsstufe`
- `Dokumente.Zugänglichkeit`

## E. Referenzen zwischen Tabellen

Der Validator prüft Verknüpfungen zwischen den Tabellen.

Beispiele:

- `Data_Template` muss auf vorhandene `Objekte` und `Merkmale` verweisen,
- Wertelisten-Referenzen müssen auf vorhandene `Werte` zeigen,
- Dokumentreferenzen müssen – wo vorgesehen – auf vorhandene `Dokumente` verweisen.

Wenn eine Referenz nicht aufgelöst werden kann, entsteht ein Fehler.

## F. URI- und Regex-Prüfungen

Bestimmte Felder werden zusätzlich formal geprüft.

Dazu gehören zum Beispiel:

- URI-Formatprüfungen,
- IFC-/bSDD-URI-Prüfungen, wo vorgesehen,
- Identifier- oder Code-Formate.

Das Ziel ist, früh zu erkennen, wenn Werte formal nicht verwendbar sind.

## G. Semantische Prüfungen

Neben der reinen Struktur werden auch logische Zusammenhänge geprüft.

Dazu gehören zum Beispiel:

- Konsistenz zwischen `Objekte`, `Merkmale`, `Werte`, `Dokumente` und `Merkmalgruppen`,
- Eindeutigkeit bzw. Duplikate,
- Konsistenz zwischen Datentyp, Werteliste, Einheit und Referenzen,
- Governance-/Metadatenprüfungen, wo diese im MVP bereits aktiv sind.

## H. Ergebnisse

Der Validator liefert drei Arten von Resultaten:

### Fehler
Müssen behoben werden. Die Datei ist in diesem Zustand nicht gültig.

### Warnungen
Sollten überprüft werden. Die Datei ist möglicherweise unvollständig oder missverständlich.

### Normalisierungen
Zeigen an, dass der Validator einen Wert automatisch interpretiert, abgeleitet oder standardisiert hat.

## Wichtiger Hinweis zum aktuellen MVP

Dieser öffentliche MVP konzentriert sich auf die **Validierung von Data Dictionaries**.

Er umfasst aktuell **nicht**:

- RDF-Erzeugung
- bSDD-Publikation
- i14y-Publikation
- LINDAS-Publikation
- sonstige Export-/Publishing-Prozesse

Diese Teile werden später separat wieder eingeführt, sobald sie repariert und getestet sind.
