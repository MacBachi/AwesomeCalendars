# AwesomeCalendars

ICS-Kalender für IT-Patchdays, Software-Releases und Konferenzen — generiert,
nicht handgepflegt.

**Abonnieren:** <https://macbachi.github.io/AwesomeCalendars/>

Die Patchday-Kalender enthalten `RRULE`-Regeln statt vorausberechneter Einzeltermine.
Sie laufen damit unbegrenzt in die Zukunft. Jedes Event trägt Quelle und
Konfidenzstufe in der Beschreibung — siehe [CONTEXT.md](CONTEXT.md) für die
Herleitung jeder Regel und die Frequenzänderungen 2026.

## Die Kalender

Abo-URL jeweils `webcal://macbachi.github.io/AwesomeCalendars/calendars/<datei>`.

### Patchdays · Sammelkalender

| Datei | Inhalt |
|---|---|
| [`patchday-all.ics`](calendars/patchday-all.ics) | alle 14 Hersteller |
| [`patchday-netzwerk.ics`](calendars/patchday-netzwerk.ics) | Cisco, Fortinet, Palo Alto Networks, Juniper, Ivanti — inklusive Cisco-Vorankündigungen |
| [`patchday-ot.ics`](calendars/patchday-ot.ics) | Siemens, Schneider Electric |

### Patchdays · einzelne Hersteller

| Datei | Regel |
|---|---|
| [`patchday-microsoft.ics`](calendars/patchday-microsoft.ics) | 2. Dienstag · plus Hotpatch-Baselines (Jan/Apr/Jul/Okt) |
| [`patchday-adobe.ics`](calendars/patchday-adobe.ics) | 2. **und 4.** Dienstag (seit 14.07.2026) |
| [`patchday-sap.ics`](calendars/patchday-sap.ics) | 2. Dienstag |
| [`patchday-oracle.ics`](calendars/patchday-oracle.ics) | 3. Dienstag · CPU quartalsweise, CSPU monatlich, inkl. Java SE |
| [`patchday-android.ics`](calendars/patchday-android.ics) | 1. Montag · Monats- und Quartals-Bulletins getrennt |
| [`patchday-cisco.ics`](calendars/patchday-cisco.ics) | 1. **und 3.** Mittwoch (seit Juli 2026) · plus Vorankündigungen |
| [`patchday-fortinet.ics`](calendars/patchday-fortinet.ics) | 2. Dienstag · Fixes seit Oktober 2026 oft schon vorher, plus Hinweistermin 10.11.2026 |
| [`patchday-paloalto.ics`](calendars/patchday-paloalto.ics) | 2. Mittwoch |
| [`patchday-juniper.ics`](calendars/patchday-juniper.ics) | 2. Mittwoch im Jan/Apr/Jul/Okt |
| [`patchday-ivanti.ics`](calendars/patchday-ivanti.ics) | 2. Dienstag |
| [`patchday-siemens.ics`](calendars/patchday-siemens.ics) | 2. Dienstag |
| [`patchday-schneider.ics`](calendars/patchday-schneider.ics) | 2. Dienstag |
| [`patchday-atlassian.ics`](calendars/patchday-atlassian.ics) | 3. Dienstag |
| [`patchday-splunk.ics`](calendars/patchday-splunk.ics) | 3. Mittwoch |

Die Kalender zeigen nur **planmäßige** Termine. Kritische, aktiv ausgenutzte Lücken
patchen Fortinet, Ivanti, Cisco, Adobe und andere außer der Reihe.

### Software-Releases — feste Daten, brauchen Nachpflege

| Datei | Inhalt | Reicht bis |
|---|---|---|
| [`releases-software.ics`](calendars/releases-software.ics) | Browser und Ubuntu zusammen | Feb 2028 |
| [`releases-browser.ics`](calendars/releases-browser.ics) | Chrome 152–173, Edge 152–166, Firefox 154–190, Extended Stable und Firefox-ESR-Wechsel | Feb 2028 |
| [`releases-ubuntu.ics`](calendars/releases-ubuntu.ics) | 26.10, wöchentliche Kernel ab 26.10.2026, 27.04 | Apr 2027 |

### Konferenzen

| Datei | Inhalt |
|---|---|
| [`conferences-security.ics`](calendars/conferences-security.ics) | 13 Security-Konferenzen bis Oktober 2027 |
| [`conferences-dach.ics`](calendars/conferences-dach.ics) | it-sa, DeepSec Wien, 40C3, secIT, Security Forum Hagenberg, TROOPERS |
| [`conferences-cloud.ics`](calendars/conferences-cloud.ics) | KubeCon North America 2026 · Europe, Japan und North America 2027 |

### Alles in einem

[`everything.ics`](calendars/everything.ics) — Patchdays inklusive aller
Hersteller-Details, Releases und Konferenzen.

## Import

Die Dateien sind ganztägige Events mit einer Erinnerung um 10:00 Uhr am Vortag.
Besser als Import ist das Abo über die Übersichtsseite — dann kommen Korrekturen
automatisch nach.

**macOS Kalender** — Datei doppelklicken, Zielkalender wählen. Vorher einen eigenen
Kalender „Patchdays" anlegen, dann lässt sich alles auf einmal wieder löschen.

**Outlook** — `Datei › Öffnen und Exportieren › Importieren/Exportieren ›
iCalendar-Datei importieren › Als neuen Kalender öffnen`.

**Google Calendar** — `Einstellungen › Importieren und Exportieren › Importieren`,
fürs Abo `Andere Kalender › Per URL`. Google expandiert `RRULE` korrekt, auch ohne
Enddatum.

Die Kalender setzen `REFRESH-INTERVAL` und `X-PUBLISHED-TTL` auf 30 Tage
(Patchdays) bzw. 7 Tage (Termine).

## Fremde Feeds, die man nicht nachbauen sollte

Diese existieren, funktionieren und sind gepflegt — abonnieren statt duplizieren.

**endoflife.date** — EOL- und Release-Daten pro Produkt, echtes Abo. Produktnamen
im Pfad tauschen (`ubuntu`, `windows`, `nodejs`, `postgresql`, …):

```
webcal://endoflife.date/calendar/php.ics
```

**CTFtime** — CTFs weltweit:

```
https://www.google.com/calendar/ical/ctftime%40gmail.com/public/basic.ics
```

Nicht empfehlenswert: `xsa.github.io/infosec-events/events.ics` enthält nur
Events aus 2022–2023, obwohl die zugehörige Website aktuell ist.

## Neu generieren

Kein Dependency, reine Standardbibliothek:

```bash
python3 generate.py
```

Ohne Erinnerungen:

```bash
python3 generate.py --no-alarms
```

Der Build ist reproduzierbar — `DTSTAMP` ist fixiert und lässt sich über
`SOURCE_DATE_EPOCH` überschreiben. Jede Regel hat ein festes `since`-Datum, ab dem
sie gilt; daraus berechnet sich `DTSTART`, das sich über Rebuilds nicht verschiebt.

Vor dem Veröffentlichen prüfen — Struktur, jede `RRULE` Tag für Tag gegen den
Generator, Stichproben gegen belegte Ist-Termine. Braucht `python-dateutil` und
`icalendar`, der Generator selbst nicht:

```bash
python3 -m venv .venv && .venv/bin/pip install python-dateutil icalendar
```

```bash
python3 generate.py && .venv/bin/python validate.py
```

Neben den `.ics`-Dateien schreibt der Generator `calendars/catalog.json`, aus dem
die Übersichtsseite ihre Liste rendert. Neue Kalender erscheinen dort also ohne
Handarbeit.

Termine und Regeln stehen als Datenstrukturen in [`generate.py`](generate.py)
(`VENDORS`, `PATCHDAYS`, `SECURITY_CONFERENCES`, …). Regeln entstehen über
`nth_weekdays((2, "TU"))` oder `weekday_between(...)`; beide liefern RRULE-Text und
dieselbe Regel als Prädikat. Jeder Eintrag verlangt `url` und `confidence`, damit
keine unbelegten Termine hineinrutschen.
