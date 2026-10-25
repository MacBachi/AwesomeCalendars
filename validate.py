#!/usr/bin/env python3
"""
Prüft die generierten Kalender, bevor sie veröffentlicht werden.

  1. Struktur      CRLF, 75-Oktett-Folding, eindeutige UIDs, parsebar
  2. Semantik      jede RRULE (expandiert mit dateutil) liefert Tag für Tag dieselben
                   Termine wie das Prädikat im Generator, 2026–2031
  3. Ist-Termine   Stichproben gegen die in CONTEXT.md belegten Veröffentlichungen
  4. Belegpflicht   kein abgeleiteter Termin; jeder Konferenztermin trägt Quelle
                   und Prüfdatum; gestrichene Termine kommen nicht zurück
  5. Abos          die veröffentlichten Abo-URLs existieren weiter

Braucht python-dateutil und icalendar (nur hier, nicht im Generator):

    python3 -m venv .venv && .venv/bin/pip install python-dateutil icalendar
    python3 generate.py && .venv/bin/python validate.py
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

from dateutil.rrule import rrulestr
from icalendar import Calendar

import generate as g

ROOT = Path(__file__).resolve().parent / "calendars"
D = dt.date
problems: list[str] = []


# 1. Struktur ---------------------------------------------------------------
files = sorted(ROOT.glob("*.ics"))
for f in files:
    raw = f.read_bytes()
    if raw.count(b"\n") != raw.count(b"\r\n"):
        problems.append(f"{f.name}: nackte LF")
    lines = raw.decode("utf-8").split("\r\n")[:-1]
    if any(len(line.encode()) > 75 for line in lines):
        problems.append(f"{f.name}: Zeile über 75 Oktette")
    uids = [line for line in lines if line.startswith("UID:")]
    if len(uids) != len(set(uids)):
        problems.append(f"{f.name}: doppelte UIDs")
    Calendar.from_ical(raw)
print(f"Struktur: {len(files)} Dateien geprüft")


# 2. RRULE gegen Prädikat ---------------------------------------------------
window_end = D(2031, 12, 31)
for ev in g.PATCHDAYS:
    start = ev.rule.first_on_or_after(ev.since)
    t0 = dt.datetime.combine(start, dt.time())
    t1 = dt.datetime.combine(window_end, dt.time())
    expanded = {d.date() for d in rrulestr(ev.rule.rrule, dtstart=t0).between(t0, t1, inc=True)}
    predicted = {start + dt.timedelta(days=i) for i in range((window_end - start).days + 1)
                 if ev.rule.matches(start + dt.timedelta(days=i))}
    if expanded != predicted:
        problems.append(f"RRULE≠Prädikat: {ev.summary}: {sorted(expanded ^ predicted)[:5]}")
print(f"RRULE-Semantik: {len(g.PATCHDAYS)} Regeln bis {window_end.year} abgeglichen")


# 3. Ist-Termine ------------------------------------------------------------
def occurs(summary: str, date: dt.date, uid_key: str = "") -> bool:
    ev = next(e for e in g.PATCHDAYS
              if e.summary == summary and (not uid_key or e.uid_key == uid_key))
    return date >= ev.since and ev.rule.matches(date)


ANDROID_SEPT = "android-security-bulletin-quartal-september"
rule_checks = [
    # (Event, Datum, erwartet, Beleg)
    ("Microsoft Patch Tuesday", D(2026, 10, 13), True, "Okt 2026"),
    ("Windows Hotpatch: Baseline-Monat (Neustart)", D(2026, 10, 13), True, "Okt-Baseline"),
    ("Windows Hotpatch: Baseline-Monat (Neustart)", D(2026, 11, 10), False, "Nov = Hotpatch"),
    ("Adobe Security Bulletins", D(2026, 7, 14), True, "Start zweimal monatlich"),
    ("Adobe Security Bulletins", D(2026, 7, 28), True, "APSB26-87/89"),
    ("Adobe Security Bulletins", D(2026, 8, 25), True, "APSB26-125"),
    ("Adobe Security Bulletins", D(2026, 9, 22), True, "APSB26-150/151"),
    ("Adobe Security Bulletins", D(2026, 10, 13), True, "Okt"),
    ("Adobe Security Bulletins", D(2026, 6, 23), False, "vor der Umstellung"),
    ("SAP Security Patch Day", D(2026, 10, 13), True, "Okt"),
    ("Oracle Critical Patch Update (CPU)", D(2026, 10, 20), True, "CPU Okt"),
    ("Oracle Critical Patch Update (CPU)", D(2027, 1, 19), True, "angekündigt"),
    ("Oracle Critical Security Patch Update (CSPU)", D(2026, 6, 16), True, "CSPU Jun"),
    ("Oracle Critical Security Patch Update (CSPU)", D(2026, 8, 18), True, "CSPU Aug"),
    ("Oracle Critical Security Patch Update (CSPU)", D(2026, 9, 15), True, "CSPU Sep"),
    ("Oracle Critical Security Patch Update (CSPU)", D(2026, 11, 17), True, "angekündigt"),
    ("Oracle Critical Security Patch Update (CSPU)", D(2026, 12, 15), True, "angekündigt"),
    ("Oracle Critical Security Patch Update (CSPU)", D(2027, 2, 16), True, "Oracle-Seite"),
    ("Oracle Critical Security Patch Update (CSPU)", D(2027, 3, 16), True, "Oracle-Seite"),
    ("Oracle Critical Patch Update (CPU)", D(2027, 7, 20), True, "Oracle-Seite"),
    ("Oracle Critical Patch Update (CPU)", D(2027, 10, 19), True, "Oracle-Seite"),
    ("Schneider Electric Security Notifications", D(2026, 1, 13), True, "SEVD-2026-013"),
    ("Schneider Electric Security Notifications", D(2026, 10, 13), True, "SEVD-2026-286"),
    ("Siemens ProductCERT Advisories", D(2026, 5, 12), True, "Siemens-Feed"),
    ("Cisco Security Advisories", D(2026, 8, 5), True, "IOS XE, SD-WAN"),
    ("Cisco Security Advisories", D(2026, 9, 2), True, "IOS XR"),
    ("Cisco Security Advisories", D(2026, 9, 16), True, "ASA/FMC/FTD"),
    ("Cisco Security Advisories", D(2026, 10, 7), True, "NX-OS"),
    ("Cisco Security Advisories", D(2026, 10, 21), True, "UC, Expressway, Snort 3"),
    ("Cisco Security Advisories", D(2026, 9, 23), False, "altes Bundle-Datum"),
    ("Cisco Vorankündigung (Advisories in 7 Tagen)", D(2026, 7, 29), True, "für 05.08."),
    ("Cisco Vorankündigung (Advisories in 7 Tagen)", D(2026, 8, 26), True, "für 02.09."),
    ("Cisco Vorankündigung (Advisories in 7 Tagen)", D(2026, 9, 9), True, "für 16.09."),
    ("Cisco Vorankündigung (Advisories in 7 Tagen)", D(2026, 10, 14), True, "für 21.10."),
    ("Fortinet PSIRT Advisories", D(2026, 10, 13), True, "Okt"),
    ("Fortinet PSIRT Advisories", D(2026, 11, 10), True, "angekündigt"),
    ("Palo Alto Networks Security Advisories", D(2026, 10, 14), True, "Okt"),
    ("Juniper Security Advisories (Quartal)", D(2026, 10, 14), True, "Okt"),
    ("Juniper Security Advisories (Quartal)", D(2026, 11, 11), False, "kein Quartalsmonat"),
    ("Atlassian Security Bulletin", D(2026, 1, 20), True, "Jan"),
    ("Atlassian Security Bulletin", D(2026, 9, 15), True, "Sep"),
    ("Atlassian Security Bulletin", D(2026, 10, 20), True, "Okt"),
    ("Splunk Security Advisories", D(2026, 4, 15), True, "Apr"),
    ("Splunk Security Advisories", D(2026, 7, 15), True, "Jul"),
    ("Splunk Security Advisories", D(2026, 10, 21), True, "SVD-2026-1007ff"),
    ("Android Security Bulletin (Monat)", D(2026, 10, 5), True, "Okt"),
    ("Android Security Bulletin (Quartal, groß)", D(2026, 12, 7), True, "Dez"),
]
for summary, date, want, why in rule_checks:
    if occurs(summary, date) != want:
        problems.append(f"Regel: {summary} am {date} soll {want} sein ({why})")
for date, want, why in [(D(2026, 9, 8), True, "Di nach Labor Day 2026"),
                        (D(2027, 9, 7), True, "Di nach Labor Day 2027"),
                        (D(2026, 9, 7), False, "Labor Day selbst")]:
    if occurs("Android Security Bulletin (Quartal, groß)", date, ANDROID_SEPT) != want:
        problems.append(f"Regel: Android September {date} soll {want} sein ({why})")

dated = g.browser_events() + g.ubuntu_events() + g.PATCHDAY_ONE_OFFS + g.ALL_EVENTS
dated_checks = [
    ("Edge 159 Stable", D(2026, 12, 10)),
    ("Edge 164 → Extended Stable", D(2027, 3, 4)),
    ("Chrome 173 Stable", D(2027, 7, 6)),
    ("Firefox 175", D(2027, 6, 29)),
    ("Firefox 190", D(2028, 2, 8)),
    ("Ubuntu 26.10 „Stonking Stingray“ Release", D(2026, 10, 15)),
    ("Fortinet: Advisories zum Security Hardening Release", D(2026, 11, 10)),
    ("FOSDEM 2027", D(2027, 1, 30)),
    ("Black Hat Asia 2027: Briefings", D(2027, 3, 2)),
    ("KubeCon + CloudNativeCon Japan 2027", D(2027, 8, 25)),
    # Österreich und Nachbarländer, Chaos, BSides (geprüft 25.10.2026)
    ("DeepSec 2026", D(2026, 11, 17)),
    ("BSides Tirol 2027", D(2027, 2, 25)),
    ("Easterhegg 2027", D(2027, 3, 26)),
    ("Grazer Linuxtage 2027", D(2027, 4, 2)),
    ("LSZ Security & Risk Management Kongress 2027", D(2027, 4, 19)),
    ("OWASP Global AppSec EU 2027", D(2027, 6, 21)),
    ("BSides Vienna 2027", D(2027, 6, 26)),
    ("IT-SECX 2027", D(2027, 10, 15)),
    ("BSides Munich 2026: Konferenz", D(2026, 11, 9)),
    ("BSides Prague 2027", D(2027, 4, 7)),
    ("BSides Budapest 2027", D(2027, 5, 13)),
    ("40C3 — Chaos Communication Congress", D(2026, 12, 27)),
    ("40C3: Voucher-Phase endet (spätestens)", D(2026, 11, 10)),
    ("Datenspuren 2027", D(2027, 9, 17)),
    ("Winterkongress 2027 der Digitalen Gesellschaft", D(2027, 3, 5)),
    ("Insomni'hack 2027", D(2027, 2, 1)),
    ("Black Hat Europe 2026", D(2026, 12, 7)),
]
for summary, date in dated_checks:
    if not any(e.summary == summary and e.start == date for e in dated):
        problems.append(f"Termin fehlt: {summary} am {date}")
print(f"Ist-Termine: {len(rule_checks) + 3} Regel- und {len(dated_checks)} Datums-Stichproben")


# 4. Belegpflicht ---------------------------------------------------------
everything = list(g.PATCHDAYS) + dated
derived = [e.summary for e in everything if e.confidence == "abgeleitet"]
problems += [f"abgeleiteter Termin: {name}" for name in derived]
for e in g.ALL_EVENTS:
    if not e.checked:
        problems.append(f"ohne Prüfdatum: {e.summary}")
    if not e.url.startswith("https://"):
        problems.append(f"ohne Quelle: {e.summary}")
    if e.end < e.start:
        problems.append(f"Ende vor Beginn: {e.summary}")
REMOVED = ["Black Hat USA 2027", "it-sa Expo & Congress 2027", "Extended Stable"]
for e in dated:
    if any(r in e.summary for r in REMOVED) and not e.summary.startswith("Edge"):
        problems.append(f"gestrichener Termin wieder da: {e.summary}")
wahrscheinlich = sum(e.confidence == "wahrscheinlich" for e in everything)
print(f"Belegpflicht: {len(everything)} Einträge, {len(derived)} abgeleitet, "
      f"{wahrscheinlich} nur wahrscheinlich")

# 5. Abos -------------------------------------------------------------------
ORIGINAL_FEEDS = ["patchday-microsoft", "patchday-adobe", "patchday-sap", "patchday-oracle",
                  "patchday-android", "patchday-cisco", "patchday-all", "releases-software",
                  "conferences-security", "conferences-cloud", "everything",
                  # seit 25.10.2026 veröffentlicht
                  "conferences-dach", "releases-browser", "releases-ubuntu",
                  "patchday-netzwerk", "patchday-ot", "patchday-fortinet"]
missing = [s for s in ORIGINAL_FEEDS if not (ROOT / f"{s}.ics").exists()]
problems += [f"Abo-URL fehlt: {s}.ics" for s in missing]
print(f"Abos: {len(ORIGINAL_FEEDS) - len(missing)}/{len(ORIGINAL_FEEDS)} ursprüngliche URLs vorhanden")

print()
print("\n".join(problems) if problems else "KEINE PROBLEME")
sys.exit(1 if problems else 0)
