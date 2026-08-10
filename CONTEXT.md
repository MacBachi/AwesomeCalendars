# CONTEXT — AwesomeCalendars

Domain-Wissen hinter den generierten Kalendern: welche Regel gilt, woher sie stammt,
und wie sicher sie ist. Stand der Recherche: **10.08.2026**.

## Grundentscheidung: Regel statt Feed

Es existiert kein gepflegter Sammel-ICS-Feed für IT-Patchdays. Kein Hersteller
(Microsoft, Oracle, SAP, Adobe, Cisco, Google) publiziert einen offiziellen
Patchday-Kalender. Die großen Konferenz-Aggregatoren (infosec-conferences.com,
dev.events, developers.events, confs.tech) bieten keinen Sammel-Export.

Patchdays sind aber deterministisch. Sie lassen sich als `RRULE` ausdrücken und
laufen dann unbegrenzt weiter, ohne Nachpflege. Genau das macht dieses Repo.
Konferenzen und Release-Termine sind es nicht — die stehen als feste Daten drin
und veralten.

## Konfidenz-Stufen

Jedes Event trägt seine Stufe in der `DESCRIPTION`.

| Stufe | Bedeutung |
|---|---|
| `bestaetigt` | Primärquelle des Herstellers, oder angekündigte Einzeltermine decken sich mit der Regel |
| `wahrscheinlich` | Sekundärquelle, plausibel und mehrfach übereinstimmend, nicht am Hersteller verifiziert |
| `abgeleitet` | Aus dem historischen Muster geschlossen, nicht offiziell angekündigt |

Datumsbasierte Events unterhalb `bestaetigt` bekommen zusätzlich `STATUS:TENTATIVE`.

## Patchday-Regeln

### Microsoft Patch Tuesday — `bestaetigt`
Zweiter Dienstag jedes Monats, Veröffentlichung gegen 10:00 Uhr Pacific Time
(= 19:00 MESZ/MEZ am selben Tag). Die Kalender-Events sind ganztägig; die Uhrzeit
steht in der Beschreibung, weil das operativ relevant ist — die Patches landen in
Europa erst am Abend.
Quelle: <https://msrc.microsoft.com/update-guide/releaseNote/>

### Adobe Security Bulletins — `wahrscheinlich`
Adobe bündelt seine planmäßigen Bulletins auf den Microsoft Patch Tuesday. Adobe
dokumentiert das nirgends als verbindliche Regel, hält es aber seit Jahren so ein.
Out-of-Band-Bulletins (Acrobat-Notfallpatches etc.) kommen zusätzlich und lassen
sich nicht kalendarisieren.
Quelle: <https://helpx.adobe.com/security/security-bulletin.html>

### SAP Security Patch Day — `bestaetigt`
Zweiter Dienstag jedes Monats. Gegengeprüft an den 2026er-Terminen
(10.02., 10.03., 14.04., 12.05., 09.06.) — Regel trifft alle.
Quelle: <https://support.sap.com/en/my-support/knowledge-base/security-notes-news.html>

### Oracle CPU — `bestaetigt`
Dritter Dienstag im Januar, April, Juli, Oktober.

Fußangel: Oracle formuliert die Regel historisch als *„Tuesday closest to the 17th"*.
Das ist **nicht** dasselbe — beginnt ein Monat an einem Mittwoch, liefert diese
Formulierung den zweiten Dienstag. Die von Oracle angekündigten Termine
(21.07.2026, 20.10.2026, 19.01.2027, 20.04.2027) folgen durchgängig dem **dritten
Dienstag**, nicht der 17.-Regel (die für Juli 2026 den 14. ergeben hätte). Dieser
Kalender folgt den tatsächlichen Terminen.
Quelle: <https://www.oracle.com/security-alerts/>

### Oracle CSPU — `abgeleitet` ⚠️
Neu seit Mai 2026: Oracle liefert in den acht Monaten ohne CPU zusätzlich einen
monatlichen Critical Security Patch Update. Der Auftakt am **28.05.2026** (ein
Donnerstag) lag außerhalb jeder Kadenz. Für die Folgemonate wird der dritte
Dienstag berichtet, ließ sich aber nicht an Oracles eigener Seite verifizieren —
`oracle.com` und `blogs.oracle.com` liefern beim automatisierten Abruf HTTP 403.

**Das ist die schwächste Regel im ganzen Repo.** Vor einem Change-Freeze bitte
gegenprüfen.
Quellen: <https://www.oracle.com/security-alerts/> ·
<https://blogs.oracle.com/security/update-monthly-critical-security-patch-updates-cspus-begin-may-28-2026>

### Android Security Bulletin — `bestaetigt`
Erster Montag jedes Monats. AOSP dokumentiert eine Ausnahme, die `RRULE` nicht
abbilden kann: fällt der erste Montag auf einen US-Feiertag, erscheint das Bulletin
am folgenden Werktag. Betrifft in der Praxis vor allem den Januar (New Year's Day
im selben Wochenumfeld) und den September (Labor Day = erster Montag im September).
Der Kalender zeigt dann einen Tag zu früh.
Quelle: <https://source.android.com/docs/security/bulletin/asb-overview>

### Cisco IOS / IOS XE Bundled Publication — `bestaetigt`
Vierter Mittwoch im März und September, halbjährlich.
Quelle: <https://sec.cloudapps.cisco.com/security/center/publicationListing.x>

**Bewusst nicht enthalten:** die separate ASA/FMC/FTD-Bundle-Veröffentlichung.
Die ist ebenfalls halbjährlich, die Monate wandern aber über die Jahre
(belegt: April 2022, Mai 2024, Oktober 2024, August 2025, März 2026). Daraus lässt
sich keine tragfähige Regel bilden — lieber kein Termin als ein falscher.

## Software-Releases

Beide Browser stellen im September 2026 von vier auf zwei Wochen um. Damit ist die
Kadenz im Umbruch und eine `RRULE` wäre falsch — hier stehen feste Daten aus den
Release-Dashboards.

- **Chrome** 152–163 (25.08.2026 – 16.02.2027), Quelle: <https://chromiumdash.appspot.com/schedule>
- **Firefox** 154–164 (18.08.2026 – 26.01.2027), Quelle: <https://whattrainisitnow.com/calendar/>
  Mozilla nennt den Zwei-Wochen-Takt ausdrücklich ein Experiment. Firefox 153 ist
  die nächste ESR-Basis (Support bis Ende 2027).
- **Ubuntu 26.10** „Stonking Stingray", 15.10.2026, neun Monate Support bis Juli 2027.
  Quelle: <https://documentation.ubuntu.com/release-notes/26.10/schedule/>

## Konferenzen

Kuratiert, **nicht vollständig**. Sieben Security- und zwei Cloud-Native-Termine,
jeweils mit Quelle und Konfidenz. Aggregator-Seiten sind hier unzuverlässig: die
für „FOSDEM 2027" ausgewiesenen Daten 31.01.–01.02. sind schlicht die 2026er-Daten,
kopiert — 2027 fällt der 31. Januar auf einen Sonntag. Deshalb steht FOSDEM hier
als `abgeleitet` mit dem ersten Februar-Wochenende (06.–07.02.2027).

`blackhat.com` und `rsaconference.com` liefern beim automatisierten Abruf HTTP 403;
beide Termine stammen aus Sekundärquellen und sind entsprechend markiert.
DEF CON 35 (05.–08.08.2027, LVCC West Hall) ist direkt von defcon.org bestätigt.

## Bewusst nicht nachgebaut

Für diese Themen existieren bereits funktionierende Abo-Feeds — die zu duplizieren
wäre schlechter als sie zu abonnieren. Siehe README.

- **EOL / Release-Daten pro Produkt** → endoflife.date, echtes Abo, sehr gepflegt
- **CTFs** → CTFtime-Google-Kalender

Nicht brauchbar: `xsa.github.io/infosec-events/events.ics` — die Website zeigt
aktuelle Events, die ICS-Datei enthält nur 2022–2023 und wird offenbar nicht mehr
regeneriert.

## Wartung

`RRULE`-Kalender laufen ohne Nachpflege weiter. Zu prüfen sind:

| Wann | Was |
|---|---|
| monatlich | Oracle CSPU — ist der dritte Dienstag die tatsächliche Kadenz? |
| quartalsweise | Chrome-/Firefox-Termine nachziehen, das Fenster läuft im Februar 2027 aus |
| jährlich | Konferenztermine des Folgejahres bestätigen, `abgeleitet` → `bestaetigt` hochstufen |
| bei Bedarf | Cisco ASA/FTD — falls Cisco doch eine feste Regel dokumentiert, aufnehmen |
