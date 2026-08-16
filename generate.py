#!/usr/bin/env python3
"""
AwesomeCalendars — Generator für IT-Patchday-, Release- und Konferenz-Kalender (RFC 5545).

Zwei Sorten Kalender:

  1. Regelbasiert  -> ein VEVENT mit RRULE, gilt unbegrenzt in die Zukunft.
                      Nur für Termine, deren Regel vom Hersteller dokumentiert ist.
  2. Datumsbasiert -> je Termin ein VEVENT mit festem Datum.
                      Für alles, was sich nicht aus einer Regel ableiten lässt.

Jedes Event trägt Quelle und Konfidenz in der DESCRIPTION. Siehe sources.md.

    python3 generate.py [--no-alarms] [--out DIR]
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

PRODID = "-//AwesomeCalendars//Patchdays, Releases & Conferences//DE"

# Reproduzierbarer Build: DTSTAMP aus SOURCE_DATE_EPOCH, sonst Stand der Recherche.
_epoch = os.environ.get("SOURCE_DATE_EPOCH")
BUILD_STAMP = (
    dt.datetime.fromtimestamp(int(_epoch), dt.timezone.utc)
    if _epoch
    else dt.datetime(2026, 8, 16, 0, 0, 0, tzinfo=dt.timezone.utc)
)
ANCHOR = BUILD_STAMP.date().replace(day=1)  # erste Wiederholung ab diesem Monat

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
    raw = line.encode("utf-8")
    if len(raw) <= 75:
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
    norm = unicodedata.normalize("NFKD", text.lower())
    norm = norm.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    keep = [c if c.isalnum() else "-" for c in norm if ord(c) < 128]
    return "-".join(filter(None, "".join(keep).split("-")))


# --------------------------------------------------------------------------- #
# Datumsarithmetik
# --------------------------------------------------------------------------- #

def nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date:
    """n-ter <weekday> im Monat (n ab 1)."""
    first = dt.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + dt.timedelta(days=offset + 7 * (n - 1))


def first_occurrence(months: list[int], weekday: str, ordinal: int, on_or_after: dt.date) -> dt.date:
    """Frühestes Vorkommen der Regel ab `on_or_after` — als DTSTART der RRULE."""
    wd = WEEKDAYS[weekday]
    year = on_or_after.year
    for candidate_year in (year, year + 1, year + 2):
        for month in sorted(months):
            occurrence = nth_weekday(candidate_year, month, wd, ordinal)
            if occurrence >= on_or_after:
                return occurrence
    raise ValueError("keine Wiederholung gefunden")


# --------------------------------------------------------------------------- #
# Datenmodell
# --------------------------------------------------------------------------- #

@dataclass
class Recurring:
    """Ein wiederkehrender Termin, ausgedrückt als RRULE."""
    summary: str
    ordinal: int                  # 1 = erster, 2 = zweiter …
    weekday: str                  # "MO" … "SU"
    months: list[int]             # [] = jeder Monat
    description: str
    url: str
    confidence: str               # bestaetigt | wahrscheinlich | abgeleitet
    categories: list[str] = field(default_factory=list)

    def rrule(self) -> str:
        byday = f"{self.ordinal}{self.weekday}"
        if not self.months:
            return f"FREQ=MONTHLY;BYDAY={byday}"
        bymonth = ",".join(str(m) for m in sorted(self.months))
        return f"FREQ=YEARLY;BYMONTH={bymonth};BYDAY={byday}"


@dataclass
class Dated:
    """Ein Termin mit festem Datum (ein- oder mehrtägig)."""
    summary: str
    start: dt.date
    end: dt.date                  # inklusiv — der letzte Tag der Veranstaltung
    description: str
    url: str
    confidence: str
    location: str = ""
    categories: list[str] = field(default_factory=list)


@dataclass
class Calendar:
    slug: str
    name: str
    description: str
    events: list                  # Recurring | Dated
    refresh_days: int = 7


CONFIDENCE_LABEL = {
    "bestaetigt": "Konfidenz: bestätigt (Primärquelle)",
    "wahrscheinlich": "Konfidenz: wahrscheinlich (Sekundärquelle, nicht am Hersteller verifiziert)",
    "abgeleitet": "Konfidenz: abgeleitet (aus dem historischen Muster, nicht offiziell angekündigt)",
}


# --------------------------------------------------------------------------- #
# Serialisierung
# --------------------------------------------------------------------------- #

def build_description(base: str, url: str, confidence: str) -> str:
    return "\n".join([base, "", CONFIDENCE_LABEL[confidence], f"Quelle: {url}"])


def alarm_lines(summary: str) -> list[str]:
    # All-Day-Event beginnt 00:00 lokal; -PT14H = 10:00 am Vortag.
    return [
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{escape(summary)}",
        "TRIGGER:-PT14H",
        "END:VALARM",
    ]


def render_recurring(ev: Recurring, cal_slug: str, alarms: bool) -> list[str]:
    start = first_occurrence(ev.months or list(range(1, 13)), ev.weekday, ev.ordinal, ANCHOR)
    uid = f"{cal_slug}-{slugify(ev.summary)}@awesomecalendars"
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{ics_utc(BUILD_STAMP)}",
        f"DTSTART;VALUE=DATE:{ics_date(start)}",
        f"DTEND;VALUE=DATE:{ics_date(start + dt.timedelta(days=1))}",
        f"RRULE:{ev.rrule()}",
        f"SUMMARY:{escape(ev.summary)}",
        f"DESCRIPTION:{escape(build_description(ev.description, ev.url, ev.confidence))}",
        f"URL:{ev.url}",
        "TRANSP:TRANSPARENT",
        "STATUS:CONFIRMED",
    ]
    if ev.categories:
        lines.append(f"CATEGORIES:{escape(','.join(ev.categories))}")
    if alarms:
        lines += alarm_lines(ev.summary)
    lines.append("END:VEVENT")
    return lines


def render_dated(ev: Dated, cal_slug: str, alarms: bool) -> list[str]:
    uid = f"{cal_slug}-{slugify(ev.summary)}-{ics_date(ev.start)}@awesomecalendars"
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
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
# Daten — Patchdays (regelbasiert)
# --------------------------------------------------------------------------- #

MICROSOFT = Recurring(
    summary="Microsoft Patch Tuesday",
    ordinal=2, weekday="TU", months=[],
    description=(
        "Monatlicher Security-Update-Release von Microsoft (Windows, Office, "
        "Exchange, SQL Server, Edge …).\n"
        "Veröffentlichung gegen 10:00 Uhr Pacific Time — das entspricht 19:00 MESZ "
        "bzw. 19:00 MEZ am selben Tag.\n"
        "Regel: zweiter Dienstag jedes Monats."
    ),
    url="https://msrc.microsoft.com/update-guide/releaseNote/",
    confidence="bestaetigt",
    categories=["Patchday", "Microsoft"],
)

ADOBE = Recurring(
    summary="Adobe Security Bulletins",
    ordinal=2, weekday="TU", months=[],
    description=(
        "Adobe veröffentlicht seine planmäßigen Security Bulletins gebündelt am "
        "Microsoft Patch Tuesday (Acrobat/Reader, Commerce, Experience Manager …).\n"
        "Außerplanmäßige Out-of-Band-Bulletins kommen zusätzlich und sind hier "
        "naturgemäß nicht enthalten.\n"
        "Regel: zweiter Dienstag jedes Monats."
    ),
    url="https://helpx.adobe.com/security/security-bulletin.html",
    confidence="wahrscheinlich",
    categories=["Patchday", "Adobe"],
)

SAP = Recurring(
    summary="SAP Security Patch Day",
    ordinal=2, weekday="TU", months=[],
    description=(
        "SAP veröffentlicht die monatlichen SAP Security Notes.\n"
        "Regel: zweiter Dienstag jedes Monats."
    ),
    url="https://support.sap.com/en/my-support/knowledge-base/security-notes-news.html",
    confidence="bestaetigt",
    categories=["Patchday", "SAP"],
)

ORACLE_CPU = Recurring(
    summary="Oracle Critical Patch Update (CPU)",
    ordinal=3, weekday="TU", months=[1, 4, 7, 10],
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
    categories=["Patchday", "Oracle"],
)

ORACLE_CSPU = Recurring(
    summary="Oracle Critical Security Patch Update (CSPU)",
    ordinal=3, weekday="TU", months=[2, 3, 5, 6, 8, 9, 11, 12],
    description=(
        "Seit Mai 2026 liefert Oracle zusätzlich in den Monaten ohne CPU einen "
        "monatlichen Critical Security Patch Update.\n"
        "Regel: dritter Dienstag in den acht Nicht-CPU-Monaten.\n"
        "Bestätigt durch die tatsächlichen Releases im Juni (16.06.2026) und "
        "August 2026 (18.08.2026) — beide dritter Dienstag.\n"
        "Einmalige Ausnahme: Der Auftakt-Release am 28.05.2026 lag außerhalb "
        "dieser Kadenz."
    ),
    url="https://www.oracle.com/security-alerts/",
    confidence="bestaetigt",
    categories=["Patchday", "Oracle"],
)

ANDROID = Recurring(
    summary="Android Security Bulletin",
    ordinal=1, weekday="MO", months=[],
    description=(
        "Monatliches Android Security Bulletin (AOSP) samt Pixel Update Bulletin.\n"
        "Regel: erster Montag jedes Monats.\n"
        "Ausnahme, die eine RRULE nicht abbilden kann: Fällt der erste Montag auf "
        "einen US-Feiertag, erscheint das Bulletin am folgenden Werktag."
    ),
    url="https://source.android.com/docs/security/bulletin/asb-overview",
    confidence="bestaetigt",
    categories=["Patchday", "Android", "Google"],
)

CISCO_IOS = Recurring(
    summary="Cisco IOS / IOS XE Bundled Publication",
    ordinal=4, weekday="WE", months=[3, 9],
    description=(
        "Halbjährliche gebündelte Security-Advisory-Veröffentlichung für Cisco "
        "IOS und IOS XE Software.\n"
        "Regel: vierter Mittwoch im März und September.\n"
        "Nicht enthalten: die separate ASA/FMC/FTD-Bundle-Veröffentlichung — deren "
        "Termine wandern und lassen sich nicht verlässlich als Regel ausdrücken. "
        "Siehe sources.md."
    ),
    url="https://sec.cloudapps.cisco.com/security/center/publicationListing.x",
    confidence="bestaetigt",
    categories=["Patchday", "Cisco"],
)

PATCHDAY_EVENTS = [MICROSOFT, ADOBE, SAP, ORACLE_CPU, ORACLE_CSPU, ANDROID, CISCO_IOS]


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
}

FIREFOX_RELEASES = {
    154: dt.date(2026, 8, 18), 155: dt.date(2026, 9, 1),
    156: dt.date(2026, 9, 15), 157: dt.date(2026, 9, 29),
    158: dt.date(2026, 10, 13), 159: dt.date(2026, 10, 27),
    160: dt.date(2026, 11, 10), 161: dt.date(2026, 11, 24),
    162: dt.date(2026, 12, 8), 163: dt.date(2027, 1, 12),
    164: dt.date(2027, 1, 26),
}


def release_events() -> list[Dated]:
    events: list[Dated] = []

    for milestone, day in CHROME_STABLE.items():
        note = ""
        if milestone >= 153:
            note = ("\nAb Chrome 153 gilt der Zwei-Wochen-Takt (vorher vier Wochen), "
                    "auf allen Plattformen inkl. Android und iOS.\n"
                    "Für Unternehmen wichtig: Der Extended-Stable-Kanal "
                    "(Windows/Mac, per Policy) bleibt beim Acht-Wochen-Rhythmus "
                    "und ist von der Umstellung nicht betroffen.")
        events.append(Dated(
            summary=f"Chrome {milestone} Stable",
            start=day, end=day,
            description=f"Google Chrome {milestone} erreicht den Stable-Channel.{note}",
            url="https://chromiumdash.appspot.com/schedule",
            confidence="bestaetigt",
            categories=["Release", "Browser", "Chrome"],
        ))

    for version, day in FIREFOX_RELEASES.items():
        note = ""
        if version >= 155:
            note = ("\nAb Firefox 155 testet Mozilla einen Zwei-Wochen-Release-Takt. "
                    "Mozilla bezeichnet das ausdrücklich als Experiment — der Plan "
                    "kann sich ändern.")
        if version == 153:
            note = "\nFirefox 153 ist die nächste ESR-Basis."
        events.append(Dated(
            summary=f"Firefox {version}",
            start=day, end=day,
            description=f"Mozilla Firefox {version} Release.{note}",
            url="https://whattrainisitnow.com/calendar/",
            confidence="bestaetigt",
            categories=["Release", "Browser", "Firefox"],
        ))

    events.append(Dated(
        summary="Ubuntu 26.10 „Stonking Stingray“ Release",
        start=dt.date(2026, 10, 15), end=dt.date(2026, 10, 15),
        description=(
            "Interim-Release mit neun Monaten Support (bis Juli 2027).\n"
            "Vorgelagerte Meilensteine: Beta 24.09.2026, Kernel Freeze 01.10.2026, "
            "Final Freeze 08.10.2026."
        ),
        url="https://documentation.ubuntu.com/release-notes/26.10/schedule/",
        confidence="bestaetigt",
        categories=["Release", "Linux", "Ubuntu"],
    ))

    return sorted(events, key=lambda e: (e.start, e.summary))


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
        summary="40C3 — Chaos Communication Congress",
        start=dt.date(2026, 12, 27), end=dt.date(2026, 12, 30),
        location="Hamburg Messe, Deutschland",
        description=(
            "40. Chaos Communication Congress des CCC.\n"
            "Der Congress liegt traditionell fest auf dem 27.–30. Dezember; die "
            "Ausgabe 2026 war zum Rechercheschluss noch nicht auf events.ccc.de "
            "final angekündigt."
        ),
        url="https://events.ccc.de/en/congress/",
        confidence="wahrscheinlich",
        categories=["Konferenz", "Security", "DACH"],
    ),
    Dated(
        summary="FOSDEM 2027",
        start=dt.date(2027, 2, 6), end=dt.date(2027, 2, 7),
        location="ULB Solbosch, Brüssel, Belgien",
        description=(
            "Free and Open Source Software Developers' European Meeting.\n"
            "Datum aus dem festen Muster abgeleitet (erstes Februar-Wochenende) — "
            "fosdem.org hatte zum Rechercheschluss noch keine 2027-Termine. "
            "Vor Reisebuchung prüfen."
        ),
        url="https://fosdem.org/",
        confidence="abgeleitet",
        categories=["Konferenz", "Open Source"],
    ),
    Dated(
        summary="RSAC Conference 2027",
        start=dt.date(2027, 4, 5), end=dt.date(2027, 4, 8),
        location="Moscone Center, San Francisco, USA",
        description="Größte kommerzielle Cybersecurity-Konferenz weltweit.",
        url="https://www.rsaconference.com/",
        confidence="wahrscheinlich",
        categories=["Konferenz", "Security"],
    ),
    Dated(
        summary="TROOPERS 2027",
        start=dt.date(2027, 6, 21), end=dt.date(2027, 6, 25),
        location="Heidelberg, Deutschland",
        description=(
            "Technische IT-Security-Konferenz von ERNW, inkl. Trainings-Tagen "
            "zu Beginn der Woche."
        ),
        url="https://troopers.de/",
        confidence="wahrscheinlich",
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
            "Termin stammt aus Sekundärquellen."
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
]

CLOUD_CONFERENCES = [
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

def vendor_slug(event: Recurring) -> str:
    return {
        "Microsoft Patch Tuesday": "microsoft",
        "Adobe Security Bulletins": "adobe",
        "SAP Security Patch Day": "sap",
        "Oracle Critical Patch Update (CPU)": "oracle",
        "Oracle Critical Security Patch Update (CSPU)": "oracle",
        "Android Security Bulletin": "android",
        "Cisco IOS / IOS XE Bundled Publication": "cisco",
    }[event.summary]


def build_catalog() -> list[Calendar]:
    calendars: list[Calendar] = []

    # Ein Kalender pro Hersteller — abonnierbar, ohne fremdes Rauschen.
    for slug in ["microsoft", "adobe", "sap", "oracle", "android", "cisco"]:
        events = [e for e in PATCHDAY_EVENTS if vendor_slug(e) == slug]
        label = events[0].categories[1]
        calendars.append(Calendar(
            slug=f"patchday-{slug}",
            name=f"Patchday · {label}",
            description=f"Planmäßige Security-Release-Termine von {label}.",
            events=events,
            refresh_days=30,
        ))

    calendars.append(Calendar(
        slug="patchday-all",
        name="Patchdays · alle Hersteller",
        description=(
            "Microsoft, Adobe, SAP, Oracle, Android und Cisco in einem Kalender. "
            "Alle Termine regelbasiert (RRULE) und damit unbegrenzt gültig."
        ),
        events=PATCHDAY_EVENTS,
        refresh_days=30,
    ))

    calendars.append(Calendar(
        slug="releases-software",
        name="Software-Releases",
        description=(
            "Geplante Release-Termine für Chrome, Firefox und Ubuntu. "
            "Feste Daten — dieser Kalender braucht regelmäßige Aktualisierung."
        ),
        events=release_events(),
        refresh_days=7,
    ))

    calendars.append(Calendar(
        slug="conferences-security",
        name="Konferenzen · IT-Security",
        description=(
            "Kuratierte Auswahl großer Security-Konferenzen. Kein Anspruch auf "
            "Vollständigkeit — jeder Termin trägt Quelle und Konfidenz."
        ),
        events=SECURITY_CONFERENCES,
        refresh_days=7,
    ))

    calendars.append(Calendar(
        slug="conferences-cloud",
        name="Konferenzen · Cloud Native",
        description="Kuratierte Auswahl großer Cloud-Native- und Kubernetes-Konferenzen.",
        events=CLOUD_CONFERENCES,
        refresh_days=7,
    ))

    calendars.append(Calendar(
        slug="everything",
        name="AwesomeCalendars · alles",
        description=(
            "Patchdays, Software-Releases und Konferenzen in einem Kalender — "
            "für alle, die nur ein Abo wollen."
        ),
        events=[*PATCHDAY_EVENTS, *release_events(), *SECURITY_CONFERENCES, *CLOUD_CONFERENCES],
        refresh_days=7,
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

    for cal in build_catalog():
        target = out_dir / f"{cal.slug}.ics"
        target.write_bytes(render_calendar(cal, alarms=not args.no_alarms).encode("utf-8"))
        print(f"{target}  ({len(cal.events)} Events)")


if __name__ == "__main__":
    main()
