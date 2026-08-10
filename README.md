# AwesomeCalendars

ICS-Kalender für IT-Patchdays, Software-Releases und Konferenzen — generiert,
nicht handgepflegt.

Die Patchday-Kalender enthalten `RRULE`-Regeln statt vorausberechneter Einzeltermine.
Sie laufen damit unbegrenzt in die Zukunft und veralten nie. Jedes Event trägt Quelle
und Konfidenzstufe in der Beschreibung — siehe [CONTEXT.md](CONTEXT.md) für die
Herleitung jeder Regel.

## Die Kalender

### Patchdays — regelbasiert, unbegrenzt gültig

| Datei | Inhalt | Regel |
|---|---|---|
| [`patchday-microsoft.ics`](calendars/patchday-microsoft.ics) | Patch Tuesday | 2. Dienstag/Monat |
| [`patchday-adobe.ics`](calendars/patchday-adobe.ics) | Security Bulletins | 2. Dienstag/Monat |
| [`patchday-sap.ics`](calendars/patchday-sap.ics) | Security Patch Day | 2. Dienstag/Monat |
| [`patchday-oracle.ics`](calendars/patchday-oracle.ics) | CPU + CSPU | 3. Dienstag, quartalsweise + monatlich |
| [`patchday-android.ics`](calendars/patchday-android.ics) | Security Bulletin | 1. Montag/Monat |
| [`patchday-cisco.ics`](calendars/patchday-cisco.ics) | IOS/IOS XE Bundle | 4. Mittwoch im März + September |
| [`patchday-all.ics`](calendars/patchday-all.ics) | alle sechs Hersteller | — |

### Termine — feste Daten, brauchen Nachpflege

| Datei | Inhalt | Reicht bis |
|---|---|---|
| [`releases-software.ics`](calendars/releases-software.ics) | Chrome 152–163, Firefox 154–164, Ubuntu 26.10 | Feb 2027 |
| [`conferences-security.ics`](calendars/conferences-security.ics) | it-sa, 40C3, FOSDEM, RSAC, TROOPERS, Black Hat, DEF CON | Aug 2027 |
| [`conferences-cloud.ics`](calendars/conferences-cloud.ics) | KubeCon EU + NA 2027 | Nov 2027 |

### Alles in einem

[`everything.ics`](calendars/everything.ics) — 40 Events, für alle, die nur ein Abo wollen.

## Import

Die Dateien sind ganztägige Events mit einer Erinnerung um 10:00 Uhr am Vortag.

**macOS Kalender** — Datei doppelklicken, Zielkalender wählen. Vorher einen eigenen
Kalender „Patchdays" anlegen, dann lässt sich alles auf einmal wieder löschen.

**Outlook** — `Datei › Öffnen und Exportieren › Importieren/Exportieren ›
iCalendar-Datei importieren › Als neuen Kalender öffnen`.

**Google Calendar** — `Einstellungen › Importieren und Exportieren › Importieren`.
Google expandiert `RRULE` korrekt, auch ohne Enddatum.

Ohne Erinnerungen neu bauen:

```bash
python3 generate.py --no-alarms
```

## Als Abo hosten

Import ist eine Kopie — Korrekturen kommen nicht nach. Für ein echtes Abo reicht
GitHub Pages: Repo pushen, Pages auf den Branch zeigen lassen, dann

```
webcal://<user>.github.io/AwesomeCalendars/calendars/patchday-all.ics
```

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

Der Build ist reproduzierbar — `DTSTAMP` ist fixiert und lässt sich über
`SOURCE_DATE_EPOCH` überschreiben, damit Regenerieren keine Diffs erzeugt.

Termine und Regeln stehen als Datenstrukturen oben in
[`generate.py`](generate.py) (`PATCHDAY_EVENTS`, `SECURITY_CONFERENCES`, …).
Zum Erweitern dort einen `Recurring`- bzw. `Dated`-Eintrag ergänzen — beide
verlangen `url` und `confidence`, damit keine unbelegten Termine hineinrutschen.
