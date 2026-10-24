#!/usr/bin/env python3
"""
AwesomeCalendars — Generator für IT-Patchday-, Release- und Konferenz-Kalender (RFC 5545).

Zwei Sorten Termine:

  1. Regelbasiert  -> ein VEVENT mit RRULE, gilt unbegrenzt in die Zukunft.
                      Nur für Termine, deren Regel vom Hersteller dokumentiert ist.
  2. Datumsbasiert -> je Termin ein VEVENT mit festem Datum.
                      Für alles, was sich nicht aus einer Regel ableiten lässt.

Jedes Event trägt Quelle und Konfidenz in der DESCRIPTION. Herleitung in CONTEXT.md.

    python3 generate.py [--no-alarms] [--out DIR]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

PRODID = "-//AwesomeCalendars//Patchdays, Releases & Conferences//DE"

# Reproduzierbarer Build: DTSTAMP aus SOURCE_DATE_EPOCH, sonst Stand der Recherche.
_epoch = os.environ.get("SOURCE_DATE_EPOCH")
BUILD_STAMP = (
    dt.datetime.fromtimestamp(int(_epoch), dt.timezone.utc)
    if _epoch
    else dt.datetime(2026, 10, 25, 0, 0, 0, tzinfo=dt.timezone.utc)
)

# Ab wann eine Regel gilt, wenn nichts anderes angegeben ist. Bestimmt das DTSTART
# und hält es über Rebuilds stabil, statt es mit jedem Build mitwandern zu lassen.
DEFAULT_SINCE = dt.date(2026, 1, 1)

WEEKDAYS = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


# --------------------------------------------------------------------------- #
# ICS-Primitive
# --------------------------------------------------------------------------- #

def escape(text: str) -> str:
    """RFC 5545 §3.3.11 — TEXT-Werte maskieren."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fold(line: str) -> list[str]:
    """RFC 5545 §3.1 — Zeilen auf 75 Oktette falten, ohne UTF-8-Zeichen zu zerschneiden."""
    if len(line.encode("utf-8")) <= 75:
        return [line]

    out: list[str] = []
    buf = bytearray()
    limit = 75
    for char in line:
        enc = char.encode("utf-8")
        if len(buf) + len(enc) > limit:
            out.append(buf.decode("utf-8"))
            buf = bytearray()
            limit = 74  # Folgezeilen beginnen mit einem Leerzeichen
        buf += enc
    if buf:
        out.append(buf.decode("utf-8"))
    return [out[0]] + [" " + part for part in out[1:]]


def ics_date(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


def ics_utc(ts: dt.datetime) -> str:
    return ts.strftime("%Y%m%dT%H%M%SZ")


def slugify(text: str) -> str:
    norm = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    norm = unicodedata.normalize("NFKD", norm)
    keep = [c if c.isalnum() else "-" for c in norm if ord(c) < 128]
    return "-".join(filter(None, "".join(keep).split("-")))


# --------------------------------------------------------------------------- #
# Wiederholungsregeln
# --------------------------------------------------------------------------- #

def nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date | None:
    """n-ter <weekday> im Monat; n = -1 ist der letzte. None, wenn es ihn nicht gibt."""
    if n > 0:
        first = dt.date(year, month, 1)
        day = first + dt.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))
    else:
        last = dt.date(year + month // 12, month % 12 + 1, 1) - dt.timedelta(days=1)
        day = last - dt.timedelta(days=(last.weekday() - weekday) % 7 + 7 * (-n - 1))
    return day if day.month == month else None


@dataclass(frozen=True)
class Rule:
    """RRULE-Text plus dieselbe Regel als Prädikat. Aus dem Prädikat berechnet sich
    DTSTART, und die Validierung prüft, dass beide dieselben Tage liefern."""
    rrule: str
    matches: Callable[[dt.date], bool]

    def first_on_or_after(self, start: dt.date) -> dt.date:
        day = start
        for _ in range(3 * 366):
            if self.matches(day):
                return day
            day += dt.timedelta(days=1)
        raise ValueError(f"keine Wiederholung für {self.rrule}")


def _bymonth(months: list[int] | None) -> str:
    return f";BYMONTH={','.join(map(str, sorted(months)))}" if months else ""


def nth_weekdays(*byday: tuple[int, str], months: list[int] | None = None) -> Rule:
    """nth_weekdays((2, "TU")) = zweiter Dienstag jedes Monats,
    nth_weekdays((2, "WE"), (-1, "WE")) = zweiter und letzter Mittwoch."""
    freq = "YEARLY" if months else "MONTHLY"
    days = ",".join(f"{n}{wd}" for n, wd in byday)

    def matches(d: dt.date) -> bool:
        if months and d.month not in months:
            return False
        return any(nth_weekday(d.year, d.month, WEEKDAYS[wd], n) == d for n, wd in byday)

    return Rule(f"FREQ={freq}{_bymonth(months)};BYDAY={days}", matches)


def weekday_between(weekday: str, first_day: int, last_day: int, months: list[int]) -> Rule:
    """Der <weekday> zwischen dem first_day. und last_day. eines Monats.
    Mit 2–8 ergibt das „den Dienstag nach dem ersten Montag“."""
    monthdays = ",".join(str(d) for d in range(first_day, last_day + 1))

    def matches(d: dt.date) -> bool:
        return (d.month in months and d.weekday() == WEEKDAYS[weekday]
                and first_day <= d.day <= last_day)

    return Rule(f"FREQ=YEARLY{_bymonth(months)};BYDAY={weekday};BYMONTHDAY={monthdays}", matches)


# --------------------------------------------------------------------------- #
# Datenmodell
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Vendor:
    slug: str
    label: str
    meta: str                       # Kurzzeile für die Übersichtsseite


@dataclass
class Recurring:
    """Ein wiederkehrender Patchday, ausgedrückt als RRULE."""
    vendor: str
    summary: str
    rule: Rule
    description: str
    url: str
    confidence: str                 # bestaetigt | wahrscheinlich | abgeleitet
    since: dt.date = DEFAULT_SINCE  # ab wann die Regel gilt
    overview: bool = True           # auch in den Sammelkalendern, nicht nur beim Hersteller
    uid_key: str = ""               # nötig, wenn zwei Events dieselbe SUMMARY tragen

    @property
    def categories(self) -> list[str]:
        return ["Patchday", VENDORS[self.vendor].label]


@dataclass
class Dated:
    """Ein Termin mit festem Datum (ein- oder mehrtägig)."""
    summary: str
    start: dt.date
    end: dt.date                    # inklusiv — der letzte Tag der Veranstaltung
    description: str
    url: str
    confidence: str
    location: str = ""
    categories: list[str] = field(default_factory=list)
    vendor: str = ""                # gesetzt = landet auch im Patchday-Kalender des Herstellers


@dataclass
class Calendar:
    slug: str
    name: str
    description: str
    events: list                    # Recurring | Dated
    group: str
    meta: str
    refresh_days: int = 7


CONFIDENCE_LABEL = {
    "bestaetigt": "Konfidenz: bestätigt (Primärquelle, oder die tatsächlichen Termine decken sich mit der Regel)",
    "wahrscheinlich": "Konfidenz: wahrscheinlich (Sekundärquelle, nicht am Hersteller verifiziert)",
    "abgeleitet": "Konfidenz: abgeleitet (aus dem Muster geschlossen, nicht offiziell angekündigt)",
}


# --------------------------------------------------------------------------- #
# Serialisierung
# --------------------------------------------------------------------------- #

def build_description(base: str, url: str, confidence: str) -> str:
    return "\n".join([base, "", CONFIDENCE_LABEL[confidence], f"Quelle: {url}"])


def alarm_lines(summary: str) -> list[str]:
    # Ganztags-Event beginnt 00:00 lokal; -PT14H = 10:00 am Vortag.
    return [
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{escape(summary)}",
        "TRIGGER:-PT14H",
        "END:VALARM",
    ]


def render_recurring(ev: Recurring, cal_slug: str, alarms: bool) -> list[str]:
    start = ev.rule.first_on_or_after(ev.since)
    lines = [
        "BEGIN:VEVENT",
        f"UID:{cal_slug}-{ev.uid_key or slugify(ev.summary)}@awesomecalendars",
        f"DTSTAMP:{ics_utc(BUILD_STAMP)}",
        f"DTSTART;VALUE=DATE:{ics_date(start)}",
        f"DTEND;VALUE=DATE:{ics_date(start + dt.timedelta(days=1))}",
        f"RRULE:{ev.rule.rrule}",
        f"SUMMARY:{escape(ev.summary)}",
        f"DESCRIPTION:{escape(build_description(ev.description, ev.url, ev.confidence))}",
        f"URL:{ev.url}",
        f"CATEGORIES:{escape(','.join(ev.categories))}",
        "TRANSP:TRANSPARENT",
        "STATUS:CONFIRMED",
    ]
    if alarms:
        lines += alarm_lines(ev.summary)
    lines.append("END:VEVENT")
    return lines


def render_dated(ev: Dated, cal_slug: str, alarms: bool) -> list[str]:
    lines = [
        "BEGIN:VEVENT",
        f"UID:{cal_slug}-{slugify(ev.summary)}-{ics_date(ev.start)}@awesomecalendars",
        f"DTSTAMP:{ics_utc(BUILD_STAMP)}",
        f"DTSTART;VALUE=DATE:{ics_date(ev.start)}",
        f"DTEND;VALUE=DATE:{ics_date(ev.end + dt.timedelta(days=1))}",
        f"SUMMARY:{escape(ev.summary)}",
        f"DESCRIPTION:{escape(build_description(ev.description, ev.url, ev.confidence))}",
        f"URL:{ev.url}",
        "TRANSP:TRANSPARENT",
        f"STATUS:{'CONFIRMED' if ev.confidence == 'bestaetigt' else 'TENTATIVE'}",
    ]
    if ev.location:
        lines.append(f"LOCATION:{escape(ev.location)}")
    if ev.categories:
        lines.append(f"CATEGORIES:{escape(','.join(ev.categories))}")
    if alarms:
        lines += alarm_lines(ev.summary)
    lines.append("END:VEVENT")
    return lines


def render_calendar(cal: Calendar, alarms: bool) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape(cal.name)}",
        f"X-WR-CALDESC:{escape(cal.description)}",
        f"REFRESH-INTERVAL;VALUE=DURATION:P{cal.refresh_days}D",
        f"X-PUBLISHED-TTL:P{cal.refresh_days}D",
    ]
    for ev in cal.events:
        if isinstance(ev, Recurring):
            lines += render_recurring(ev, cal.slug, alarms)
        else:
            lines += render_dated(ev, cal.slug, alarms)
    lines.append("END:VCALENDAR")

    folded: list[str] = []
    for line in lines:
        folded.extend(fold(line))
    return "\r\n".join(folded) + "\r\n"


# --------------------------------------------------------------------------- #
# Daten — Hersteller
# --------------------------------------------------------------------------- #

VENDORS = {v.slug: v for v in [
    Vendor("microsoft", "Microsoft", "2. Dienstag · 10:00 PT = 19:00 Uhr MEZ/MESZ · Hotpatch-Baselines"),
    Vendor("adobe", "Adobe", "2. + 4. Dienstag · zweimal monatlich seit Juli 2026"),
    Vendor("sap", "SAP", "2. Dienstag"),
    Vendor("oracle", "Oracle", "3. Dienstag · CPU quartalsweise, CSPU monatlich · inkl. Java SE"),
    Vendor("android", "Android", "1. Montag · große Bulletins im März, Juni, September, Dezember"),
    Vendor("cisco", "Cisco", "1. + 3. Mittwoch · 16:00 UTC · Vorankündigung 7 Tage vorher"),
    Vendor("fortinet", "Fortinet", "2. Dienstag · Fixes seit Oktober 2026 oft vorab als Hardening Release"),
    Vendor("paloalto", "Palo Alto Networks", "2. Mittwoch · 09:00 PT"),
    Vendor("juniper", "Juniper", "2. Mittwoch im Januar, April, Juli, Oktober"),
    Vendor("ivanti", "Ivanti", "2. Dienstag"),
    Vendor("siemens", "Siemens", "2. Dienstag · ProductCERT, Industrie/OT"),
    Vendor("schneider", "Schneider Electric", "2. Dienstag · Industrie/OT"),
    Vendor("atlassian", "Atlassian", "3. Dienstag · Jira, Confluence, Bitbucket"),
    Vendor("splunk", "Splunk", "3. Mittwoch · zugleich ein Cisco-Termin"),
]}

NETWORK_VENDORS = ["cisco", "fortinet", "paloalto", "juniper", "ivanti"]
OT_VENDORS = ["siemens", "schneider"]


# --------------------------------------------------------------------------- #
# Daten — Patchdays (regelbasiert)
# --------------------------------------------------------------------------- #

PATCHDAYS = [
    # --- Microsoft ---------------------------------------------------------
    Recurring(
        vendor="microsoft",
        summary="Microsoft Patch Tuesday",
        rule=nth_weekdays((2, "TU")),
        description=(
            "Monatlicher Security-Update-Release von Microsoft (Windows, Office, "
            "Exchange, SQL Server, Edge …).\n"
            "Veröffentlichung gegen 10:00 Uhr Pacific Time — in Mitteleuropa 19:00 Uhr "
            "am selben Tag. Liegt der Termin im März zwischen der US-Umstellung auf "
            "Sommerzeit (zweiter Sonntag) und der europäischen (letzter Sonntag), ist "
            "es 18:00 Uhr — das betrifft die meisten, aber nicht alle Jahre.\n"
            "Seit 28.07.2026 sammelt Windows 11 alle neustartpflichtigen Updates und "
            "installiert sie zusammen mit diesem Release — ein Neustart im Monat, und "
            "zwar hier.\n"
            "Regel: zweiter Dienstag jedes Monats."
        ),
        url="https://msrc.microsoft.com/update-guide/releaseNote/",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="microsoft",
        summary="Windows Hotpatch: Baseline-Monat (Neustart)",
        rule=nth_weekdays((2, "TU"), months=[1, 4, 7, 10]),
        description=(
            "Für Windows 11 Enterprise und Windows Server mit Hotpatch: In diesen "
            "Monaten kommt das reguläre kumulative Update, die Geräte müssen neu "
            "starten. In den beiden Folgemonaten kommen Hotpatches ohne Neustart.\n"
            "Regel: Patch Tuesday im Januar, April, Juli und Oktober.\n"
            "2026 wich Microsoft davon ab: zusätzliche Baseline im Juni, und der "
            "September-Release kam als Standard-Update mit Neustartpflicht. Der "
            "nächste neustartfreie Zyklus beginnt laut Microsoft im November 2026."
        ),
        url="https://techcommunity.microsoft.com/blog/windows-itpro-blog/hotpatch-for-client-frequently-asked-questions/4413582",
        confidence="bestaetigt",
        overview=False,
    ),

    # --- Adobe -------------------------------------------------------------
    Recurring(
        vendor="adobe",
        summary="Adobe Security Bulletins",
        rule=nth_weekdays((2, "TU"), (4, "TU")),
        since=dt.date(2026, 7, 14),
        description=(
            "Seit 14.07.2026 veröffentlicht Adobe Security Bulletins und Advisories "
            "zweimal im Monat statt einmal. Der zweite Dienstag fällt weiter auf den "
            "Microsoft Patch Tuesday, der vierte Dienstag ist neu.\n"
            "Begründung von Adobe: KI beschleunigt das Finden von Schwachstellen, die "
            "Zeit zwischen Veröffentlichung und Ausnutzung schrumpft von Tagen auf "
            "Stunden.\n"
            "Aktiv ausgenutzte Lücken und Zero-Days kommen weiterhin außer der Reihe "
            "und stehen naturgemäß nicht hier.\n"
            "Regel: zweiter und vierter Dienstag jedes Monats."
        ),
        url="https://blog.adobe.com/security/protecting-customers-faster-how-adobe-is-responding-to-ai-accelerated-vulnerability-discovery",
        confidence="bestaetigt",
    ),

    # --- SAP ---------------------------------------------------------------
    Recurring(
        vendor="sap",
        summary="SAP Security Patch Day",
        rule=nth_weekdays((2, "TU")),
        description=(
            "SAP veröffentlicht die monatlichen SAP Security Notes.\n"
            "Regel: zweiter Dienstag jedes Monats."
        ),
        url="https://support.sap.com/en/my-support/knowledge-base/security-notes-news.html",
        confidence="bestaetigt",
    ),

    # --- Oracle ------------------------------------------------------------
    Recurring(
        vendor="oracle",
        summary="Oracle Critical Patch Update (CPU)",
        rule=nth_weekdays((3, "TU"), months=[1, 4, 7, 10]),
        description=(
            "Vierteljährliches Oracle Critical Patch Update — der große, "
            "produktübergreifende Sammel-Release (Database, Java SE, Fusion "
            "Middleware, E-Business Suite, MySQL …).\n"
            "Regel: dritter Dienstag im Januar, April, Juli und Oktober.\n"
            "Hinweis: Oracle formuliert die Regel historisch als 'Dienstag, der dem "
            "17. am nächsten liegt'. Die tatsächlich angekündigten Termine "
            "(21.07.2026, 20.10.2026, 19.01.2027, 20.04.2027) folgen dem dritten "
            "Dienstag; danach ist dieser Kalender gebaut."
        ),
        url="https://www.oracle.com/security-alerts/",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="oracle",
        summary="Oracle Critical Security Patch Update (CSPU)",
        rule=nth_weekdays((3, "TU"), months=[2, 3, 5, 6, 8, 9, 11, 12]),
        since=dt.date(2026, 6, 1),
        description=(
            "Seit Mai 2026 liefert Oracle in den acht Monaten ohne CPU einen "
            "monatlichen Critical Security Patch Update.\n"
            "Regel: dritter Dienstag in den Nicht-CPU-Monaten. Bestätigt durch Juni "
            "(16.06.), August (18.08.) und September 2026 (15.09.); die nächsten "
            "beiden hat Oracle für den 17.11. und 15.12.2026 angekündigt. Einmalige "
            "Ausnahme war der Auftakt am 28.05.2026.\n"
            "Java SE: Oracle zieht auch Java in den Monatsrhythmus. Bestätigt ist ein "
            "Java-Update am 18.08.2026, angekündigt ist der 17.11.2026; für 2027 plant "
            "Oracle mehrere monatliche Java-Updates."
        ),
        url="https://www.oracle.com/security-alerts/",
        confidence="bestaetigt",
    ),

    # --- Android -----------------------------------------------------------
    Recurring(
        vendor="android",
        summary="Android Security Bulletin (Monat)",
        rule=nth_weekdays((1, "MO"), months=[1, 2, 4, 5, 7, 8, 10, 11]),
        description=(
            "Monatliches Android Security Bulletin. Seit Googles Umstellung auf "
            "risikobasierte Updates enthalten die Monate zwischen den Quartals-"
            "Releases nur noch Hochrisiko-Lücken — aktiv ausgenutzt oder Teil einer "
            "bekannten Exploit-Kette. Manche Bulletins enthalten null Fixes.\n"
            "Regel: erster Montag. Fällt er auf einen US-Feiertag, erscheint das "
            "Bulletin am folgenden Werktag."
        ),
        url="https://source.android.com/docs/security/bulletin/asb-overview",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="android",
        summary="Android Security Bulletin (Quartal, groß)",
        rule=nth_weekdays((1, "MO"), months=[3, 6, 12]),
        description=(
            "Großes Quartals-Bulletin, abgestimmt auf Androids Quartals-Release-Plan. "
            "Hier landet der Großteil der Fixes (September 2026: 180 CVEs).\n"
            "Regel: erster Montag im März, Juni und Dezember. September steht als "
            "eigener Termin im Kalender, weil dort immer Labor Day dazwischenliegt."
        ),
        url="https://source.android.com/docs/security/bulletin/asb-overview",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="android",
        summary="Android Security Bulletin (Quartal, groß)",
        uid_key="android-security-bulletin-quartal-september",
        rule=weekday_between("TU", 2, 8, months=[9]),
        description=(
            "Großes Quartals-Bulletin im September (2026: 180 CVEs).\n"
            "Der erste Montag im September ist immer Labor Day, ein US-Feiertag. "
            "Nach Googles eigener Regel erscheint das Bulletin dann am folgenden "
            "Werktag.\n"
            "Regel: der Dienstag zwischen dem 2. und 8. September."
        ),
        url="https://source.android.com/docs/security/bulletin/asb-overview",
        confidence="bestaetigt",
    ),

    # --- Cisco -------------------------------------------------------------
    Recurring(
        vendor="cisco",
        summary="Cisco Security Advisories",
        rule=nth_weekdays((1, "WE"), (3, "WE")),
        since=dt.date(2026, 7, 1),
        description=(
            "Seit Juli 2026 bündelt Cisco Security Advisories und „Security Hardening "
            "Releases“ auf den ersten und dritten Mittwoch, 16:00 UTC (17:00 Uhr MEZ, "
            "18:00 Uhr MESZ).\n"
            "Die Kern-Betriebssysteme (IOS XE, IOS XR, NX-OS, ASA/FTD, SD-WAN) kommen "
            "quartalsweise und gestaffelt dran, nie zwei am selben Termin. Bisher: "
            "IOS XE und SD-WAN am 05.08.2026, IOS XR am 02.09.2026, ASA/FMC/FTD am "
            "16.09.2026, NX-OS am 07.10.2026. Am 21.10.2026 folgten Unified "
            "Communications, Expressway und Snort 3.\n"
            "Welche Produkte betroffen sind, kündigt Cisco sieben Tage vorher an — "
            "auch wenn an einem Termin gar nichts kommt.\n"
            "Die alten Halbjahres-Bundles (IOS/IOS XE im März und September, FXOS/"
            "NX-OS, IOS XR, ASA/FTD) sind damit abgelöst. Die letzten erschienen im "
            "Februar und März 2026."
        ),
        url="https://sec.cloudapps.cisco.com/security/center/resources/risk-based-disclosure",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="cisco",
        summary="Cisco Vorankündigung (Advisories in 7 Tagen)",
        rule=nth_weekdays((2, "WE"), (-1, "WE")),
        since=dt.date(2026, 6, 24),
        description=(
            "Sieben Tage vor jedem Veröffentlichungstermin listet Cisco, welche "
            "Produkte und Plattformen drankommen. Das ist der eigentliche "
            "Planungstermin für Changes.\n"
            "Regel: zweiter und letzter Mittwoch jedes Monats — jeweils eine Woche "
            "vor dem dritten bzw. dem nächsten ersten Mittwoch."
        ),
        url="https://sec.cloudapps.cisco.com/security/center/publicationListing.x",
        confidence="bestaetigt",
        overview=False,
    ),

    # --- Netzwerk & Security-Appliances ------------------------------------
    Recurring(
        vendor="fortinet",
        summary="Fortinet PSIRT Advisories",
        rule=nth_weekdays((2, "TU")),
        description=(
            "Fortinet bündelt alle Advisories bis einschließlich Schweregrad „High“ "
            "auf den zweiten Dienstag, veröffentlicht während der Geschäftszeit an "
            "der US-Westküste — in Mitteleuropa also am Abend.\n"
            "Kritische Lücken kommen außer der Reihe (Out-of-Cycle) und stehen nicht "
            "hier. Bei FortiOS war das in der Vergangenheit häufig der Fall.\n"
            "Neu seit Oktober 2026: Fortinet liefert Fixes aus eigener KI-gestützter "
            "Prüfung zuerst als „Security Hardening Release“ aus und veröffentlicht "
            "die Advisories erst am nächsten zweiten Dienstag. Fortinet kündigt an, "
            "so weiterzuarbeiten, nennt aber keinen festen Termin für die Releases "
            "selbst. Die gefixten Versionen können also vor diesem Termin da sein.\n"
            "Regel: zweiter Dienstag jedes Monats."
        ),
        url="https://www.fortiguard.com/psirt_policy",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="paloalto",
        summary="Palo Alto Networks Security Advisories",
        rule=nth_weekdays((2, "WE")),
        description=(
            "Advisories erscheinen am zweiten Mittwoch um 09:00 Uhr Pacific Time — "
            "18:00 Uhr in Mitteleuropa. Liegt der Termin im März zwischen der US- und "
            "der europäischen Sommerzeitumstellung, ist es 17:00 Uhr.\n"
            "Veröffentlicht wird erst, wenn Fixes für alle unterstützten Versionen "
            "bereitstehen. Ausnahme: kritische, aktiv ausgenutzte Lücken.\n"
            "Regel: zweiter Mittwoch jedes Monats."
        ),
        url="https://www.paloaltonetworks.com/product-security-assurance",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="juniper",
        summary="Juniper Security Advisories (Quartal)",
        rule=nth_weekdays((2, "WE"), months=[1, 4, 7, 10]),
        description=(
            "Juniper SIRT veröffentlicht nicht dringende Advisories für alle "
            "Juniper-Produkte gebündelt viermal im Jahr.\n"
            "Außer der Reihe nur bei aktiver Ausnutzung oder koordinierten "
            "Multi-Vendor-Themen.\n"
            "Regel: zweiter Mittwoch im Januar, April, Juli und Oktober."
        ),
        url="https://www.juniper.net/documentation/us/en/software/juniper-routing-director2.8.0/user-guide/topics/concept/sirt-advisories-overview.html",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="ivanti",
        summary="Ivanti Security Advisories",
        rule=nth_weekdays((2, "TU")),
        description=(
            "Ivanti veröffentlicht planmäßige Security-Updates (u. a. Connect Secure, "
            "Policy Secure, EPMM, Endpoint Manager) am Microsoft Patch Tuesday.\n"
            "Kritische, aktiv ausgenutzte Lücken kommen außer der Reihe.\n"
            "Regel: zweiter Dienstag jedes Monats."
        ),
        url="https://www.ivanti.com/blog/september-2026-security-update",
        confidence="wahrscheinlich",
    ),

    # --- Industrie / OT ----------------------------------------------------
    Recurring(
        vendor="siemens",
        summary="Siemens ProductCERT Advisories",
        rule=nth_weekdays((2, "TU")),
        description=(
            "Siemens veröffentlicht Security Advisories für Industrie- und "
            "Automatisierungsprodukte gebündelt am zweiten Dienstag, dem "
            "sogenannten ICS Patch Tuesday.\n"
            "Regel: zweiter Dienstag jedes Monats."
        ),
        url="https://www.securityweek.com/ics-patch-tuesday-security-advisories-released-by-siemens-schneider-cisa-others/",
        confidence="wahrscheinlich",
    ),
    Recurring(
        vendor="schneider",
        summary="Schneider Electric Security Notifications",
        rule=nth_weekdays((2, "TU")),
        description=(
            "Schneider Electric veröffentlicht Security Notifications einmal im Monat "
            "am zweiten Dienstag, damit Kunden Patches einplanen können.\n"
            "Regel: zweiter Dienstag jedes Monats."
        ),
        url="https://www.se.com/ww/en/work/support/cybersecurity/vulnerability-policy/",
        confidence="bestaetigt",
    ),

    # --- Enterprise-Software -----------------------------------------------
    Recurring(
        vendor="atlassian",
        summary="Atlassian Security Bulletin",
        rule=nth_weekdays((3, "TU")),
        description=(
            "Monatliches Security Bulletin für Jira, Confluence, Bitbucket & Co. "
            "Enthält nur Lücken, die Atlassian als nicht kritisch einstuft.\n"
            "Kritische Lücken kommen als separate Critical Security Advisory außer "
            "der Reihe.\n"
            "Regel: dritter Dienstag jedes Monats — 2026 von Januar bis September "
            "ausnahmslos eingehalten."
        ),
        url="https://confluence.atlassian.com/security/security-advisories-bulletins-1236937381.html",
        confidence="bestaetigt",
    ),
    Recurring(
        vendor="splunk",
        summary="Splunk Security Advisories",
        rule=nth_weekdays((3, "WE")),
        description=(
            "Splunk veröffentlicht Advisories laut eigener FAQ „in der Regel“ am "
            "dritten Mittwoch, einige Wochen nachdem die Fixes bereitstehen.\n"
            "Der dritte Mittwoch ist zugleich ein Cisco-Termin; Splunk gehört zu "
            "Cisco. Belegt 2026: 15.04., 15.07., 19.08. und 21.10.\n"
            "Einmalige Abweichung: Die für den 16.09.2026 geplanten Advisories kamen "
            "verschoben am 07.10.2026.\n"
            "Regel: dritter Mittwoch jedes Monats."
        ),
        url="https://advisory.splunk.com/faqs",
        confidence="bestaetigt",
    ),
]

# Einzeltermine, die zu einem Hersteller gehören, aber keiner Regel folgen.
PATCHDAY_ONE_OFFS = [
    Dated(
        summary="Fortinet: Advisories zum Security Hardening Release",
        start=dt.date(2026, 11, 10), end=dt.date(2026, 11, 10),
        description=(
            "Am 21.10.2026 hat Fortinet ein Security Hardening Release mit kritischen "
            "und hochgradigen Fixes angekündigt. Die Versionen sind seit 22.10.2026 "
            "verfügbar, CVEs und Advisories folgen erst an diesem Patch Tuesday.\n"
            "Gefixte Versionen: FortiOS 8.0.2, 7.6.8, 7.4.13, 7.2.14 · FortiManager "
            "und FortiAnalyzer 8.0.2, 7.6.8, 7.4.12, 7.2.13 · FortiMail 8.0.2, 7.6.7, "
            "7.4.9 (7.2 muss auf 7.4 oder neuer) · FortiAuthenticator 8.0.4, 6.6.11.\n"
            "Fortinet rät, internetseitige Geräte zuerst und vor diesem Termin zu "
            "aktualisieren — ab der Veröffentlichung sind die Details öffentlich."
        ),
        url="https://www.fortinet.com/blog/ciso-collective/fortinet-releases-security-hardening-release-for-multiple-products",
        confidence="bestaetigt",
        categories=["Patchday", "Fortinet"],
        vendor="fortinet",
    ),
    Dated(
        summary="Splunk Security Advisories (verschoben)",
        start=dt.date(2026, 10, 7), end=dt.date(2026, 10, 7),
        description=(
            "Die ursprünglich für den 16.09.2026 geplanten Advisories für Splunk "
            "Enterprise, Universal Forwarder, Add-on for AWS und Splunk MCP Server."
        ),
        url="https://advisory.splunk.com/advisories/SVD-2026-0901",
        confidence="bestaetigt",
        categories=["Patchday", "Splunk"],
        vendor="splunk",
    ),
]


# --------------------------------------------------------------------------- #
# Daten — Software-Releases (datumsbasiert)
# --------------------------------------------------------------------------- #

CHROME_STABLE = {
    152: dt.date(2026, 8, 25), 153: dt.date(2026, 9, 8),
    154: dt.date(2026, 9, 22), 155: dt.date(2026, 10, 6),
    156: dt.date(2026, 10, 20), 157: dt.date(2026, 11, 3),
    158: dt.date(2026, 11, 17), 159: dt.date(2026, 12, 8),
    160: dt.date(2027, 1, 5), 161: dt.date(2027, 1, 19),
    162: dt.date(2027, 2, 2), 163: dt.date(2027, 2, 16),
    164: dt.date(2027, 3, 2), 165: dt.date(2027, 3, 16),
    166: dt.date(2027, 3, 30), 167: dt.date(2027, 4, 13),
    168: dt.date(2027, 4, 27), 169: dt.date(2027, 5, 11),
    170: dt.date(2027, 5, 25), 171: dt.date(2027, 6, 8),
    172: dt.date(2027, 6, 22), 173: dt.date(2027, 7, 6),
}

# Jedes vierte Milestone wird Extended Stable und bleibt acht Wochen.
# 156 und 160 sind für Chrome berichtet, die späteren folgen aus dem Muster.
CHROME_EXTENDED = {156: "wahrscheinlich", 160: "wahrscheinlich",
                   164: "abgeleitet", 168: "abgeleitet", 172: "abgeleitet"}

# Microsoft nennt Release-Wochen; das Datum ist der Donnerstag der Woche bzw. der
# tatsächliche Release-Tag.
EDGE_STABLE = {
    152: dt.date(2026, 8, 27), 153: dt.date(2026, 9, 10),
    154: dt.date(2026, 9, 24), 155: dt.date(2026, 10, 8),
    156: dt.date(2026, 10, 22), 157: dt.date(2026, 11, 5),
    158: dt.date(2026, 11, 19), 159: dt.date(2026, 12, 10),
    160: dt.date(2027, 1, 7), 161: dt.date(2027, 1, 21),
    162: dt.date(2027, 2, 4), 163: dt.date(2027, 2, 18),
    164: dt.date(2027, 3, 4), 165: dt.date(2027, 3, 18),
    166: dt.date(2027, 4, 1),
}
EDGE_EXTENDED = [152, 156, 160, 164]

FIREFOX_RELEASES = {
    154: dt.date(2026, 8, 18), 155: dt.date(2026, 9, 1),
    156: dt.date(2026, 9, 15), 157: dt.date(2026, 9, 29),
    158: dt.date(2026, 10, 13), 159: dt.date(2026, 10, 27),
    160: dt.date(2026, 11, 10), 161: dt.date(2026, 11, 24),
    162: dt.date(2026, 12, 8), 163: dt.date(2027, 1, 12),
    164: dt.date(2027, 1, 26), 165: dt.date(2027, 2, 9),
    166: dt.date(2027, 2, 23), 167: dt.date(2027, 3, 9),
    168: dt.date(2027, 3, 23), 169: dt.date(2027, 4, 6),
    170: dt.date(2027, 4, 20), 171: dt.date(2027, 5, 4),
    172: dt.date(2027, 5, 18), 173: dt.date(2027, 6, 1),
    174: dt.date(2027, 6, 15), 175: dt.date(2027, 6, 29),
    176: dt.date(2027, 7, 13), 177: dt.date(2027, 7, 27),
    178: dt.date(2027, 8, 10), 179: dt.date(2027, 8, 24),
    180: dt.date(2027, 9, 7), 181: dt.date(2027, 9, 21),
    182: dt.date(2027, 10, 5), 183: dt.date(2027, 10, 19),
    184: dt.date(2027, 11, 2), 185: dt.date(2027, 11, 16),
    186: dt.date(2027, 11, 30), 187: dt.date(2027, 12, 14),
    188: dt.date(2028, 1, 11), 189: dt.date(2028, 1, 25),
    190: dt.date(2028, 2, 8),
}

# Was im Mozilla-Kalender an ESR-Wechseln ablesbar ist.
FIREFOX_ESR_NOTES = {
    168: "Mit diesem Release erscheint laut Mozilla-Kalender das letzte Update für "
         "ESR 115 (115.53) — die Linie, die als letzte noch Windows 7, 8 und 8.1 "
         "sowie ältere macOS-Versionen unterstützt.",
    175: "Neue ESR-Basis: Zusammen mit Firefox 175 erscheint ESR 175.0. Bis "
         "September 2027 laufen ESR 153 und ESR 175 parallel — Zeit für den "
         "Umstieg in verwalteten Umgebungen.",
    180: "Mit diesem Release erscheint laut Mozilla-Kalender das letzte Update für "
         "ESR 153 (153.27). Danach ist ESR 175 die einzige ESR-Linie.",
}


def _span(versions: dict) -> str:
    return f"{min(versions)}–{max(versions)}"


def browser_events() -> list[Dated]:
    events: list[Dated] = []

    for milestone, day in CHROME_STABLE.items():
        note = ""
        if milestone >= 153:
            note = ("\nSeit Chrome 153 (08.09.2026) gilt der Zwei-Wochen-Takt auf allen "
                    "Plattformen inklusive Android und iOS.")
        events.append(Dated(
            summary=f"Chrome {milestone} Stable",
            start=day, end=day,
            description=f"Google Chrome {milestone} erreicht den Stable-Kanal.{note}",
            url="https://chromiumdash.appspot.com/schedule",
            confidence="bestaetigt",
            categories=["Release", "Browser", "Chrome"],
        ))

    for milestone, confidence in CHROME_EXTENDED.items():
        day = CHROME_STABLE[milestone]
        events.append(Dated(
            summary=f"Chrome {milestone} → Extended Stable",
            start=day, end=day,
            description=(
                f"Chrome {milestone} wird Extended Stable und bleibt dort acht Wochen. "
                "Der Kanal ist für verwaltete Windows- und macOS-Umgebungen gedacht "
                "und wird per Policy aktiviert. Er ist von der Umstellung auf zwei "
                "Wochen nicht betroffen und springt jeweils um vier Milestones.\n"
                "Google selbst veröffentlicht keine Extended-Stable-Termine; 156 und "
                "160 sind berichtet, die folgenden sind aus dem Muster abgeleitet. "
                "Microsoft bestätigt für Edge offiziell dasselbe Muster (152, 156, "
                "160, 164)."
            ),
            url="https://support.google.com/chrome/a/answer/16942104",
            confidence=confidence,
            categories=["Release", "Browser", "Chrome", "Enterprise"],
        ))

    for version, day in EDGE_STABLE.items():
        events.append(Dated(
            summary=f"Edge {version} Stable",
            start=day, end=day,
            description=(
                f"Microsoft Edge {version}: Beginn des progressiven Rollouts im "
                "Stable-Kanal, typischerweise zwei Tage nach Chrome.\n"
                "Seit Edge 152 (27.08.2026) im Zwei-Wochen-Takt. Künftige Termine "
                "nennt Microsoft als Release-Woche und als ungefähr — Edge 159 hat "
                "Microsoft im Oktober 2026 bereits um eine Woche auf den 10.12. "
                "verschoben."
            ),
            url="https://learn.microsoft.com/en-us/deployedge/microsoft-edge-release-schedule",
            confidence="bestaetigt",
            categories=["Release", "Browser", "Edge"],
        ))

    for version in EDGE_EXTENDED:
        day = EDGE_STABLE[version]
        events.append(Dated(
            summary=f"Edge {version} → Extended Stable",
            start=day, end=day,
            description=(
                f"Edge {version} wird Extended Stable. Der Kanal folgt einem "
                "Acht-Wochen-Zyklus und nimmt jedes vierte Release (152, 156, 160, "
                "164 …). Nur für verwaltete Umgebungen."
            ),
            url="https://learn.microsoft.com/en-us/deployedge/microsoft-edge-release-schedule",
            confidence="bestaetigt",
            categories=["Release", "Browser", "Edge", "Enterprise"],
        ))

    for version, day in FIREFOX_RELEASES.items():
        note = ""
        if version >= 155:
            note = ("\nSeit Firefox 155 (01.09.2026) im Zwei-Wochen-Takt, von Mozilla "
                    "bei der Ankündigung als Experiment bezeichnet. Sicherheits-"
                    "Zwischenreleases kommen zusätzlich.")
        if version in FIREFOX_ESR_NOTES:
            note += "\n" + FIREFOX_ESR_NOTES[version]
        events.append(Dated(
            summary=f"Firefox {version}",
            start=day, end=day,
            description=f"Mozilla Firefox {version} Release.{note}",
            url="https://whattrainisitnow.com/calendar/",
            confidence="bestaetigt",
            categories=["Release", "Browser", "Firefox"],
        ))

    return sorted(events, key=lambda e: (e.start, e.summary))


def ubuntu_events() -> list[Dated]:
    return [
        Dated(
            summary="Ubuntu 26.10 „Stonking Stingray“ Release",
            start=dt.date(2026, 10, 15), end=dt.date(2026, 10, 15),
            description=(
                "Interim-Release mit neun Monaten Support (bis Juli 2027).\n"
                "Letzte Meilensteine: Kernel Freeze 01.10.2026, Final Freeze und "
                "Release Candidate 08.10.2026."
            ),
            url="https://documentation.ubuntu.com/release-notes/26.10/schedule/",
            confidence="bestaetigt",
            categories=["Release", "Linux", "Ubuntu"],
        ),
        Dated(
            summary="Ubuntu-Kernel: ab jetzt wöchentliche Releases",
            start=dt.date(2026, 10, 26), end=dt.date(2026, 10, 26),
            description=(
                "Canonical ersetzt den bisherigen 4/2-Rhythmus (alle vier Wochen ein "
                "reguläres Kernel-Update, Notfall-Updates nach zwei Wochen) durch "
                "überlappende Zwei-Wochen-Zyklen. Effektiv erscheint ab hier jede "
                "Woche ein neuer Kernel. Übergangszyklen starteten am 28.09. und "
                "12.10.2026.\n"
                "Grund ist die CVE-Flut im Kernel, nach Canonical stark durch "
                "KI-gestützte Fehlersuche getrieben: Linux 7.2 behob über 1.500 CVEs, "
                "frühere Versionen rund 500.\n"
                "Wer Kernel-Updates manuell einspielt, braucht damit ein wöchentliches "
                "Wartungsfenster oder Livepatch."
            ),
            url="https://canonical.com/blog/accelerating-delivery-of-cve-fixes-with-a-new-kernel-release-strategy",
            confidence="wahrscheinlich",
            categories=["Release", "Linux", "Ubuntu", "Kernel"],
        ),
        Dated(
            summary="Ubuntu 27.04 Release",
            start=dt.date(2027, 4, 22), end=dt.date(2027, 4, 22),
            description=(
                "Interim-Release mit neun Monaten Support. Der Codename ist noch nicht "
                "vergeben, Canonical führt es als „T T“.\n"
                "Meilensteine: Feature Freeze 25.02.2027, Beta 01.04.2027, Kernel "
                "Freeze 08.04.2027, Final Freeze und Release Candidate 15.04.2027."
            ),
            url="https://documentation.ubuntu.com/release-notes/27.04/schedule/",
            confidence="bestaetigt",
            categories=["Release", "Linux", "Ubuntu"],
        ),
    ]


# --------------------------------------------------------------------------- #
# Daten — Konferenzen (datumsbasiert, kuratiert)
# --------------------------------------------------------------------------- #

SECURITY_CONFERENCES = [
    Dated(
        summary="it-sa Expo & Congress 2026",
        start=dt.date(2026, 10, 27), end=dt.date(2026, 10, 29),
        location="Messezentrum Nürnberg, Deutschland",
        description="Größte IT-Security-Fachmesse im deutschsprachigen Raum.",
        url="https://www.itsa365.de/en/it-sa-expo-congress/exhibition-info",
        confidence="bestaetigt",
        categories=["Konferenz", "Security", "DACH"],
    ),
    Dated(
        summary="DeepSec 2026",
        start=dt.date(2026, 11, 17), end=dt.date(2026, 11, 20),
        location="Renaissance Hotel, Wien, Österreich",
        description=(
            "DeepSec In-Depth Security Conference in Wien, technisch und "
            "herstellerneutral. Trainings am 17. und 18.11., Konferenz am 19. und "
            "20.11."
        ),
        url="https://deepsec.net/",
        confidence="bestaetigt",
        categories=["Konferenz", "Security", "DACH"],
    ),
    Dated(
        summary="Black Hat Europe 2026",
        start=dt.date(2026, 12, 7), end=dt.date(2026, 12, 10),
        location="ExCeL London, Großbritannien",
        description=(
            "Trainings ab 07.12., Briefings, Arsenal und Business Hall am "
            "09. und 10.12.\n"
            "blackhat.com war beim automatisierten Abruf nicht erreichbar (403) — "
            "Termin stammt aus übereinstimmenden Sekundärquellen."
        ),
        url="https://blackhat.com/europe/",
        confidence="wahrscheinlich",
        categories=["Konferenz", "Security"],
    ),
    Dated(
        summary="40C3 — Chaos Communication Congress",
        start=dt.date(2026, 12, 27), end=dt.date(2026, 12, 30),
        location="Hamburg Messe, Deutschland",
        description=(
            "40. Chaos Communication Congress, Motto „Model Citizens“. Zum Jubiläum "
            "erstmals in den Hallen der Hamburg Messe statt im CCH.\n"
            "Einreichungsschluss für Beiträge: 09.10.2026."
        ),
        url="https://www.ccc.de/en/updates/2026/40c3-model-citizens",
        confidence="bestaetigt",
        categories=["Konferenz", "Security", "DACH"],
    ),
    Dated(
        summary="FOSDEM 2027",
        start=dt.date(2027, 1, 30), end=dt.date(2027, 1, 31),
        location="ULB Solbosch, Brüssel, Belgien",
        description=(
            "Free and Open Source Software Developers' European Meeting. "
            "Eintritt frei, keine Registrierung."
        ),
        url="https://fosdem.org/2027/news/fosdem-2027-dates/",
        confidence="bestaetigt",
        categories=["Konferenz", "Open Source"],
    ),
    Dated(
        summary="Black Hat Asia 2027",
        start=dt.date(2027, 2, 28), end=dt.date(2027, 3, 3),
        location="Marina Bay Sands, Singapur",
        description=(
            "Trainings am 28.02. und 01.03., Briefings am 02. und 03.03.\n"
            "blackhat.com war beim automatisierten Abruf nicht erreichbar (403) — "
            "Termin stammt aus übereinstimmenden Sekundärquellen."
        ),
        url="https://blackhat.com/asia/",
        confidence="wahrscheinlich",
        categories=["Konferenz", "Security"],
    ),
    Dated(
        summary="secIT by heise 2027",
        start=dt.date(2027, 3, 9), end=dt.date(2027, 3, 11),
        location="Hannover Congress Centrum, Deutschland",
        description=(
            "IT-Security-Konferenz und Fachausstellung von heise. 09.03. Workshops, "
            "10. und 11.03. Konferenz und Ausstellung."
        ),
        url="https://secit-heise.de/",
        confidence="wahrscheinlich",
        categories=["Konferenz", "Security", "DACH"],
    ),
    Dated(
        summary="RSAC Conference 2027",
        start=dt.date(2027, 4, 5), end=dt.date(2027, 4, 8),
        location="Moscone Center, San Francisco, USA",
        description="Größte kommerzielle Cybersecurity-Konferenz weltweit.",
        url="https://www.moscone.com/events/rsac-2027-conference",
        confidence="bestaetigt",
        categories=["Konferenz", "Security"],
    ),
    Dated(
        summary="Security Forum Hagenberg 2027",
        start=dt.date(2027, 5, 19), end=dt.date(2027, 5, 20),
        location="FH Oberösterreich, Campus Hagenberg, Österreich",
        description=(
            "Etablierte österreichische Fachkonferenz für Informationssicherheit, "
            "organisiert von Studierenden der FH Oberösterreich."
        ),
        url="https://www.securityforum.at/",
        confidence="bestaetigt",
        categories=["Konferenz", "Security", "DACH"],
    ),
    Dated(
        summary="TROOPERS 2027",
        start=dt.date(2027, 6, 21), end=dt.date(2027, 6, 25),
        location="Heidelberg, Deutschland",
        description=(
            "Technische IT-Security-Konferenz von ERNW. Trainings am 21. und 22.06., "
            "Konferenz vom 23. bis 25.06."
        ),
        url="https://troopers.de/",
        confidence="bestaetigt",
        categories=["Konferenz", "Security", "DACH"],
    ),
    Dated(
        summary="Black Hat USA 2027",
        start=dt.date(2027, 7, 31), end=dt.date(2027, 8, 5),
        location="Mandalay Bay Convention Center, Las Vegas, USA",
        description=(
            "Trainings und Briefings. Die Briefings bilden traditionell die "
            "letzten beiden Tage.\n"
            "blackhat.com war beim automatisierten Abruf nicht erreichbar (403) — "
            "Termin stammt aus übereinstimmenden Sekundärquellen."
        ),
        url="https://blackhat.com/upcoming.html",
        confidence="wahrscheinlich",
        categories=["Konferenz", "Security"],
    ),
    Dated(
        summary="DEF CON 35",
        start=dt.date(2027, 8, 5), end=dt.date(2027, 8, 8),
        location="Las Vegas Convention Center West Hall, Las Vegas, USA",
        description="Direkt im Anschluss an die Black Hat USA Briefings.",
        url="https://defcon.org/",
        confidence="bestaetigt",
        categories=["Konferenz", "Security"],
    ),
    Dated(
        summary="it-sa Expo & Congress 2027",
        start=dt.date(2027, 10, 5), end=dt.date(2027, 10, 7),
        location="Messezentrum Nürnberg, Deutschland",
        description="Größte IT-Security-Fachmesse im deutschsprachigen Raum.",
        url="https://www.pressebox.de/events/nuernbergmesse-gmbh/it-sa-2027/eventid/62575",
        confidence="bestaetigt",
        categories=["Konferenz", "Security", "DACH"],
    ),
]

CLOUD_CONFERENCES = [
    Dated(
        summary="KubeCon + CloudNativeCon North America 2026",
        start=dt.date(2026, 11, 9), end=dt.date(2026, 11, 12),
        location="Salt Palace Convention Center, Salt Lake City, USA",
        description=(
            "Flaggschiff-Konferenz der CNCF für Nordamerika. Co-located Events am "
            "09.11., darunter ArgoCon, BackstageCon und CiliumCon."
        ),
        url="https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/",
        confidence="bestaetigt",
        categories=["Konferenz", "Cloud Native", "Kubernetes"],
    ),
    Dated(
        summary="KubeCon + CloudNativeCon Europe 2027",
        start=dt.date(2027, 3, 15), end=dt.date(2027, 3, 18),
        location="Barcelona, Spanien",
        description="Flaggschiff-Konferenz der CNCF für Europa.",
        url="https://events.linuxfoundation.org/kubecon-cloudnativecon-europe-2027/",
        confidence="bestaetigt",
        categories=["Konferenz", "Cloud Native", "Kubernetes"],
    ),
    Dated(
        summary="KubeCon + CloudNativeCon Japan 2027",
        start=dt.date(2027, 8, 25), end=dt.date(2027, 8, 26),
        location="Yokohama, Japan",
        description="Regionale CNCF-Konferenz für Japan.",
        url="https://events.linuxfoundation.org/kubecon-cloudnativecon-japan/",
        confidence="bestaetigt",
        categories=["Konferenz", "Cloud Native", "Kubernetes"],
    ),
    Dated(
        summary="KubeCon + CloudNativeCon North America 2027",
        start=dt.date(2027, 11, 8), end=dt.date(2027, 11, 11),
        location="New Orleans, Louisiana, USA",
        description="Flaggschiff-Konferenz der CNCF für Nordamerika.",
        url="https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/",
        confidence="bestaetigt",
        categories=["Konferenz", "Cloud Native", "Kubernetes"],
    ),
]


# --------------------------------------------------------------------------- #
# Zusammenstellung
# --------------------------------------------------------------------------- #

GROUP_BUNDLES = "Patchdays · Sammelkalender"
GROUP_VENDORS = "Patchdays · einzelne Hersteller"
GROUP_RELEASES = "Software-Releases"
GROUP_CONFERENCES = "Konferenzen"
GROUP_ALL = "Alles in einem"


def vendor_events(slugs: list[str], overview_only: bool) -> list:
    recurring = [e for e in PATCHDAYS
                 if e.vendor in slugs and (e.overview or not overview_only)]
    one_offs = [e for e in PATCHDAY_ONE_OFFS if e.vendor in slugs]
    return recurring + one_offs


def build_catalog() -> list[Calendar]:
    calendars: list[Calendar] = []

    calendars.append(Calendar(
        slug="patchday-all",
        name="Patchdays · alle Hersteller",
        description=(
            f"Planmäßige Security-Releases von {len(VENDORS)} Herstellern in einem "
            "Kalender, regelbasiert und damit unbegrenzt gültig. Hersteller-Details "
            "wie Ciscos Vorankündigungen stehen nur in den Einzelkalendern."
        ),
        events=vendor_events(list(VENDORS), overview_only=True),
        group=GROUP_BUNDLES,
        meta=" · ".join(v.label for v in VENDORS.values()),
        refresh_days=30,
    ))
    calendars.append(Calendar(
        slug="patchday-netzwerk",
        name="Patchdays · Netzwerk & Security-Appliances",
        description="Cisco, Fortinet, Palo Alto Networks, Juniper und Ivanti.",
        events=vendor_events(NETWORK_VENDORS, overview_only=False),
        group=GROUP_BUNDLES,
        meta=" · ".join(VENDORS[s].label for s in NETWORK_VENDORS) + " · inkl. Cisco-Vorankündigungen",
        refresh_days=30,
    ))
    calendars.append(Calendar(
        slug="patchday-ot",
        name="Patchdays · Industrie & OT",
        description="Siemens ProductCERT und Schneider Electric.",
        events=vendor_events(OT_VENDORS, overview_only=False),
        group=GROUP_BUNDLES,
        meta=" · ".join(VENDORS[s].label for s in OT_VENDORS) + " · „ICS Patch Tuesday“",
        refresh_days=30,
    ))

    for vendor in VENDORS.values():
        calendars.append(Calendar(
            slug=f"patchday-{vendor.slug}",
            name=f"Patchday · {vendor.label}",
            description=f"Planmäßige Security-Release-Termine von {vendor.label}.",
            events=vendor_events([vendor.slug], overview_only=False),
            group=GROUP_VENDORS,
            meta=vendor.meta,
            refresh_days=30,
        ))

    browsers, ubuntu = browser_events(), ubuntu_events()
    calendars.append(Calendar(
        slug="releases-software",
        name="Software-Releases",
        description=(
            "Chrome, Edge, Firefox und Ubuntu. Feste Daten — dieser Kalender wird "
            "regelmäßig nachgezogen."
        ),
        events=sorted(browsers + ubuntu, key=lambda e: (e.start, e.summary)),
        group=GROUP_RELEASES,
        meta="Browser und Ubuntu zusammen",
    ))
    calendars.append(Calendar(
        slug="releases-browser",
        name="Releases · Browser",
        description="Chrome, Edge und Firefox, inklusive Extended-Stable-Wechseln.",
        events=browsers,
        group=GROUP_RELEASES,
        meta=(f"Chrome {_span(CHROME_STABLE)} · Edge {_span(EDGE_STABLE)} · "
              f"Firefox {_span(FIREFOX_RELEASES)} · Extended Stable und ESR"),
    ))
    calendars.append(Calendar(
        slug="releases-ubuntu",
        name="Releases · Ubuntu",
        description="Ubuntu-Releases und Änderungen am Kernel-Update-Rhythmus.",
        events=ubuntu,
        group=GROUP_RELEASES,
        meta="26.10 · wöchentliche Kernel ab 26.10.2026 · 27.04",
    ))

    calendars.append(Calendar(
        slug="conferences-security",
        name="Konferenzen · IT-Security",
        description=(
            "Kuratierte Auswahl großer Security-Konferenzen. Kein Anspruch auf "
            "Vollständigkeit — jeder Termin trägt Quelle und Konfidenz."
        ),
        events=SECURITY_CONFERENCES,
        group=GROUP_CONFERENCES,
        meta=(f"{len(SECURITY_CONFERENCES)} Termine bis "
              f"{max(e.end for e in SECURITY_CONFERENCES):%m/%Y}"),
    ))
    dach = [e for e in SECURITY_CONFERENCES if "DACH" in e.categories]
    calendars.append(Calendar(
        slug="conferences-dach",
        name="Konferenzen · DACH",
        description="Security-Konferenzen in Deutschland und Österreich.",
        events=dach,
        group=GROUP_CONFERENCES,
        meta="it-sa · DeepSec Wien · 40C3 · secIT · Security Forum Hagenberg · TROOPERS",
    ))
    calendars.append(Calendar(
        slug="conferences-cloud",
        name="Konferenzen · Cloud Native",
        description="Kuratierte Auswahl großer Cloud-Native- und Kubernetes-Konferenzen.",
        events=CLOUD_CONFERENCES,
        group=GROUP_CONFERENCES,
        meta="KubeCon North America 2026 · Europe, Japan und North America 2027",
    ))

    everything = [
        *vendor_events(list(VENDORS), overview_only=False),
        *sorted(browsers + ubuntu, key=lambda e: (e.start, e.summary)),
        *SECURITY_CONFERENCES,
        *CLOUD_CONFERENCES,
    ]
    calendars.append(Calendar(
        slug="everything",
        name="AwesomeCalendars · alles",
        description=(
            "Patchdays, Software-Releases und Konferenzen in einem Kalender — "
            "für alle, die nur ein Abo wollen."
        ),
        events=everything,
        group=GROUP_ALL,
        meta=f"{len(everything)} Einträge — Patchdays, Releases und Konferenzen",
    ))

    return calendars


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="calendars", help="Zielverzeichnis")
    parser.add_argument("--no-alarms", action="store_true",
                        help="ohne VALARM (Erinnerung 10:00 Uhr am Vortag)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    catalog = build_catalog()
    for cal in catalog:
        target = out_dir / f"{cal.slug}.ics"
        target.write_bytes(render_calendar(cal, alarms=not args.no_alarms).encode("utf-8"))
        print(f"{target}  ({len(cal.events)} Events)")

    # Die Übersichtsseite (index.html) rendert ihre Liste aus dieser Datei.
    manifest = [
        {"file": f"{cal.slug}.ics", "name": cal.name, "meta": cal.meta,
         "group": cal.group, "events": len(cal.events)}
        for cal in catalog
    ]
    (out_dir / "catalog.json").write_text(
        json.dumps({"updated": BUILD_STAMP.date().isoformat(), "calendars": manifest},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
