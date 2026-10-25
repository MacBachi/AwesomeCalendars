# CONTEXT — AwesomeCalendars

Domain-Wissen hinter den generierten Kalendern: welche Regel gilt, woher sie stammt,
und wie sicher sie ist. Stand der Recherche: **25.10.2026**.

## Grundentscheidung: Regel statt Feed

Es existiert kein gepflegter Sammel-ICS-Feed für IT-Patchdays. Kein Hersteller
publiziert einen offiziellen Patchday-Kalender. Die großen Konferenz-Aggregatoren
(infosec-conferences.com, dev.events, developers.events, confs.tech) bieten keinen
Sammel-Export.

Patchdays folgen aber festen Regeln. Als `RRULE` laufen sie unbegrenzt weiter, ohne
dass jemand Einzeltermine nachträgt. Konferenzen und Release-Termine folgen keiner
Regel — die stehen als feste Daten drin und veralten.

**Was 2026 gelehrt hat:** Die Regeln sind stabil, aber nicht ewig. Zwischen Mai und
Oktober 2026 haben sechs Hersteller ihr Vorgehen geändert, alle mit derselben
Begründung — KI-gestützte Fehlersuche erzeugt mehr CVEs, und die Zeit bis zur
Ausnutzung schrumpft. Ein `RRULE`-Kalender braucht deshalb keine Pflege der
Termine, wohl aber eine regelmäßige Recherche, ob die Regel noch gilt.

## Frequenzänderungen 2026

| Hersteller | Vorher | Seit | Jetzt |
|---|---|---|---|
| Oracle | CPU quartalsweise | Mai 2026 | zusätzlich CSPU in allen Nicht-CPU-Monaten; Java SE folgt |
| Cisco | Halbjahres-Bundles je Betriebssystem | Juli 2026 | 1. + 3. Mittwoch, Kern-OS quartalsweise gestaffelt |
| Adobe | 2. Dienstag | 14.07.2026 | 2. + 4. Dienstag |
| Chrome | vier Wochen | 08.09.2026 | zwei Wochen (Extended Stable bleibt bei acht) |
| Edge | vier Wochen | 27.08.2026 | zwei Wochen (Extended Stable bleibt bei acht) |
| Firefox | vier Wochen | 01.09.2026 | zwei Wochen, ausdrücklich als Experiment |
| Ubuntu-Kernel | 4/2-Zyklus | 26.10.2026 | wöchentlich |
| Android | monatlich, alles | 2025 | monatlich nur Hochrisiko, Rest quartalsweise |
| Windows 11 | Neustart je Update | 28.07.2026 | Neustarts auf den Patch Tuesday gebündelt |
| Fortinet | Fix und Advisory gleichzeitig | 21.10.2026 | Fixes zuerst als Hardening Release, Advisories am nächsten 2. Dienstag |

## Belegpflicht

**Kein Termin ist erfunden, jeder ist geprüft.** Seit dem 25.10.2026 gilt das als
harte Regel für das ganze Repo:

- Ein Termin kommt nur rein, wenn er an der Seite oder in einer Pressemitteilung
  des Veranstalters bzw. Herstellers steht, oder sich aus deren eigenen Daten
  ergibt (Beispiel Schneider: Advisory-Nummern mit Veröffentlichungstag).
- Abgeleitete Termine („war die letzten Jahre immer im Juni") gibt es nicht mehr.
  Was sich nicht belegen lässt, bleibt draußen und steht unten unter
  *Geprüft, aber nicht aufgenommen*.
- Auch Nebenangaben in Beschreibungen — „erste Ausgabe", Trainingstage, Uhrzeiten,
  Veranstaltungsorte — stehen nur drin, wenn die Quelle sie nennt.
- Jeder Konferenztermin trägt Quelle und Prüfdatum in der Beschreibung.
- `validate.py` erzwingt das: kein Eintrag mit Konfidenz `abgeleitet`, keiner ohne
  Quelle oder Prüfdatum, gestrichene Termine dürfen nicht zurückkommen.

Was beim Durchgang am 25.10.2026 deshalb **gestrichen** wurde:

| Termin | Grund |
|---|---|
| Black Hat USA 2027 (31.07.–05.08.) | nur Sekundärquellen; blackhat.com blockt automatische Abrufe und ist im eingebauten Browser per Site-Berechtigung gesperrt, die Abschluss-Pressemitteilung 2026 nennt 2027 nicht |
| it-sa 2027 (05.–07.10.) | Veranstalter (AUMA-Eintrag der NürnbergMesse) nennt nur „Oktober 2027" |
| Chrome Extended Stable 156–172 | Google veröffentlicht keine Termine; 164/168/172 waren aus dem Muster abgeleitet |
| Black Hat Asia 2027, Trainingstage | nur die Briefings (02.–03.03.) stehen im offiziellen CFP-Dokument |

## Konfidenz-Stufen

Jedes Event trägt seine Stufe in der `DESCRIPTION`. Nach der Bereinigung vom
25.10.2026 tragen alle Einträge `bestaetigt`.

| Stufe | Bedeutung |
|---|---|
| `bestaetigt` | Primärquelle des Herstellers, oder die tatsächlichen Termine decken sich mit der Regel |
| `wahrscheinlich` | Sekundärquelle — derzeit nicht verwendet |
| `abgeleitet` | Aus dem Muster geschlossen — nicht mehr zulässig, `validate.py` lehnt es ab |

Datumsbasierte Events unterhalb `bestaetigt` bekämen zusätzlich `STATUS:TENTATIVE`.

Mehrere Seiten (`blackhat.com`, `se.com`, `rsaconference.com`) blocken automatische
Abrufe mit HTTP 403. In diesen Fällen ist der Termin über eine andere
Primärquelle belegt (Pressemitteilung, offizielles Dokument, Herstellerdaten) —
oder er steht nicht im Kalender.

## Patchday-Regeln

### Microsoft Patch Tuesday — `bestaetigt`
Zweiter Dienstag, Veröffentlichung gegen 10:00 Uhr Pacific Time. In Mitteleuropa
ist das 19:00 Uhr. Ausnahme **März**: Die USA stellen am zweiten Sonntag auf
Sommerzeit um, Europa erst am letzten. Liegt der Patch Tuesday in dieser Lücke,
kommt er um 18:00 Uhr. Das ist meist so, aber nicht immer — 2027 liegt der Termin
am 09.03., vor der US-Umstellung am 14.03., und bleibt bei 19:00 Uhr (nachgerechnet
mit `zoneinfo` für 2026–2031). Im November gibt es keine Lücke, weil der zweite
Dienstag immer nach der US-Rückstellung liegt.

Seit 28.07.2026 bündelt Windows 11 alle neustartpflichtigen Updates und installiert
sie mit dem Patch Tuesday — ein Neustart im Monat. Notfall-Updates (Defender,
kritische Fixes) bleiben ausgenommen.
Quelle (Wortlaut „second Tuesday of each month, typically at 10:00 AM Pacific
Time"): <https://learn.microsoft.com/en-us/windows/deployment/update/release-cycle>

### Windows Hotpatch-Baseline — `bestaetigt`
Für Windows 11 Enterprise und Windows Server mit Hotpatch: Baseline mit Neustart
im Januar, April, Juli und Oktober, dazwischen zwei neustartfreie Hotpatch-Monate.

2026 hielt Microsoft das zweimal nicht ein: eine zusätzliche Baseline im Juni,
und im September kam ein Standard-Update mit Neustartpflicht, weil Kernkomponenten
betroffen waren. Oktober ist ohnehin Baseline; der nächste neustartfreie Zyklus
beginnt laut Microsoft im November 2026. Die Regel im Kalender beschreibt den
Normalfall.

Nur im Microsoft-Einzelkalender, nicht in den Sammelkalendern — der Termin fällt
immer auf den Patch Tuesday und würde dort nur doppeln.
Quelle: <https://techcommunity.microsoft.com/blog/windows-itpro-blog/hotpatch-for-client-frequently-asked-questions/4413582>

### Adobe Security Bulletins — `bestaetigt`
**Seit 14.07.2026 zweiter und vierter Dienstag.** Angekündigt am 25.06.2026 von
Adobes CSO. Belegt am vierten Dienstag: 28.07. (APSB26-87, -89), 25.08. (APSB26-125),
22.09.2026 (u. a. APSB26-150, -151). Die Bulletins dort sind kleiner, der große
Block bleibt am zweiten Dienstag. Vorher bündelte Adobe auf den Microsoft Patch Tuesday, ohne das als
Regel zu dokumentieren — deshalb stand Adobe hier bis Oktober nur als
`wahrscheinlich` und nur mit dem zweiten Dienstag. Die Hälfte der Termine fehlte.

Aktiv ausgenutzte Lücken und Zero-Days kommen weiterhin Out-of-Band.
Quelle: <https://blog.adobe.com/security/protecting-customers-faster-how-adobe-is-responding-to-ai-accelerated-vulnerability-discovery>

### SAP Security Patch Day — `bestaetigt`
Zweiter Dienstag. Gegengeprüft an allen 2026er-Terminen bis Oktober (13.10.2026).
Quelle: <https://support.sap.com/en/my-support/knowledge-base/security-notes-news.html>

### Oracle CPU — `bestaetigt`
Dritter Dienstag im Januar, April, Juli, Oktober — so steht es wörtlich auf
Oracles Security-Alerts-Seite, zusammen mit den nächsten vier Terminen
(19.01., 20.04., 20.07., 19.10.2027). Der Kalender liefert genau diese vier.

Historisch formulierte Oracle die Regel als *„Tuesday closest to the 17th"* — das
ergibt in Monaten, die an einem Mittwoch beginnen, den zweiten Dienstag. Die
heutige Formulierung und alle Termine folgen dem dritten Dienstag.
Quelle: <https://www.oracle.com/security-alerts/>

### Oracle CSPU — `bestaetigt`
Seit Mai 2026 in allen acht Nicht-CPU-Monaten, dritter Dienstag. Oracle nennt die
Regel inzwischen wörtlich auf der Security-Alerts-Seite und listet die nächsten
vier Termine: 17.11. und 15.12.2026, 16.02. und 16.03.2027.

| Release | Datum | Dritter Dienstag? |
|---|---|---|
| Mai 2026 (Auftakt) | 28.05.2026, Donnerstag | nein — einmalige Ausnahme |
| Juni 2026 | 16.06.2026 | ✅ |
| *Juli 2026* | *CPU-Monat* | — |
| August 2026 | 18.08.2026 | ✅ |
| September 2026 | 15.09.2026 | ✅ |
| *Oktober 2026* | *CPU-Monat, CPU am 20.10.* | — |
| November / Dezember 2026 | 17.11. / 15.12. — von Oracle angekündigt | ✅ |

**Java SE** zieht Oracle ebenfalls in den Monatsrhythmus: monatliches Java-Update
am 18.08.2026, angekündigt für den 17.11.2026 (ein CSPU-Termin), für 2027 „mehrere"
monatliche Updates. Java hängt damit an den Oracle-Terminen, braucht keinen
eigenen Kalender — kommt aber nicht in jedem CSPU-Monat.
Quellen: <https://www.oracle.com/security-alerts/cspusep2026.html> ·
<https://blogs.oracle.com/java/transitioning-java-to-more-frequent-security-updates>

### Android Security Bulletin — `bestaetigt`
Erster Montag. Seit Googles Umstellung auf **risikobasierte Updates** sind die
Bulletins ungleich groß: Monatlich kommen nur noch Hochrisiko-Lücken (aktiv
ausgenutzt oder Teil einer Exploit-Kette), manche Bulletins enthalten null Fixes.
Der Großteil landet in den Quartals-Bulletins im März, Juni, September und
Dezember (September 2026: 180 CVEs). Der Kalender führt die beiden deshalb als
getrennte Termine.

**September-Sonderfall, jetzt korrekt abgebildet:** Der erste Montag im September
ist immer Labor Day. Nach Googles Regel erscheint das Bulletin dann am folgenden
Werktag. Der Kalender modelliert das mit
`FREQ=YEARLY;BYMONTH=9;BYDAY=TU;BYMONTHDAY=2,3,4,5,6,7,8` — dem Dienstag nach
dem ersten Montag. Am echten Termin geprüft: Das September-Bulletin 2026 trägt
„Published September 8, 2026", ein Dienstag. Bis Oktober 2026 zeigte der Kalender
hier einen Tag zu früh.

Verbleibende Ungenauigkeit: Fällt der erste Montag im Januar auf Neujahr (2029,
2035) oder im Juli auf den beobachteten Independence Day (05.07.2027), verschiebt
Google wohl ebenfalls — das ist selten genug, um es nicht zu modellieren.
Quelle: <https://source.android.com/docs/security/bulletin/asb-overview>

### Cisco — `bestaetigt`
**Komplett neu seit Juli 2026.** Cisco veröffentlicht Security Advisories und
„Security Hardening Releases" am **ersten und dritten Mittwoch**, 16:00 UTC.
Angekündigt am 02.06.2026 im Cisco-Security-Blog.

Die Kern-Betriebssysteme kommen quartalsweise und gestaffelt dran, nie zwei am
selben Termin. Belegt bisher:

| Termin | Inhalt |
|---|---|
| 05.08.2026 (1. Mi) | IOS XE, Catalyst SD-WAN |
| 02.09.2026 (1. Mi) | IOS XR |
| 16.09.2026 (3. Mi) | ASA, FMC, FTD |
| 07.10.2026 (1. Mi) | NX-OS (Nexus, MDS, UCS Fabric Interconnects) |
| 21.10.2026 (3. Mi) | Unified Communications, Expressway, Snort 3 |

Welcher Termin welches OS trifft, lässt sich nicht vorausberechnen. Dafür
veröffentlicht Cisco **sieben Tage vorher** eine Vorankündigung mit der
Produktliste — auch wenn an einem Termin nichts kommt. Diese Vorankündigungen
stehen als eigener Termin im Cisco-Kalender: zweiter und letzter Mittwoch, denn
der letzte Mittwoch eines Monats liegt immer genau eine Woche vor dem ersten des
nächsten. Belegt: 29.07., 26.08., 09.09., 14.10.2026.

**Die Halbjahres-Bundles sind abgeschafft.** Das betraf den bisherigen Kalender
direkt: Er zeigte das IOS/IOS-XE-Bundle für den 23.09.2026 (vierter Mittwoch im
September). An dem Tag kam nichts — IOS XE war bereits am 05.08. dran. Die letzten
Bundles erschienen im Februar (FXOS/NX-OS) und März 2026 (IOS/IOS XE, IOS XR,
ASA/FTD). Ciscos Security Vulnerability Policy listet die Bundles noch, ist in
dem Punkt aber veraltet; die Event-Response-Liste zeigt danach keine mehr.
Quellen: <https://sec.cloudapps.cisco.com/security/center/resources/risk-based-disclosure> ·
<https://blogs.cisco.com/security/strengthening-the-foundation-a-predictable-customer-focused-response-to-ai-accelerated-vulnerability-discovery>

### Fortinet — `bestaetigt`
Zweiter Dienstag, während der US-Westküsten-Geschäftszeit. Gebündelt wird alles
bis einschließlich „High"; **Critical kommt außer der Reihe** — bei FortiOS in der
Vergangenheit oft. Der Kalender deckt also gerade die gefährlichsten
Fortinet-Lücken nicht ab.

**Neu seit 21.10.2026: Fixes vor Advisories.** Fortinets CISO kündigte ein
„Security Hardening Release" mit kritischen und hochgradigen Fixes aus eigener
KI-gestützter Prüfung an. Die Versionen kamen am 22.10.2026 (FortiOS 8.0.2, 7.6.8,
7.4.13, 7.2.14 · FortiManager und FortiAnalyzer 8.0.2, 7.6.8, 7.4.12, 7.2.13 ·
FortiMail 8.0.2, 7.6.7, 7.4.9 · FortiAuthenticator 8.0.4, 6.6.11), die Advisories
mit CVEs folgen erst am Patch Tuesday, 10.11.2026. Fortinet schreibt, der
Release-Prozess ändere sich damit „going forward". Eine feste Regel für die
Hardening Releases selbst gibt es nicht — der zweite Dienstag bleibt der Termin
für die Advisories, die Fixes können schon Wochen vorher da sein. Der 10.11. steht
als eigener Einzeltermin mit den Versionen im Fortinet-Kalender.
Quellen: <https://www.fortiguard.com/psirt_policy> ·
<https://www.fortinet.com/blog/ciso-collective/fortinet-releases-security-hardening-release-for-multiple-products>

### Palo Alto Networks — `bestaetigt`
Zweiter Mittwoch, 09:00 Uhr Pacific Time — 18:00 Uhr in Mitteleuropa. In der
März-Lücke zwischen US- und EU-Sommerzeitumstellung 17:00 Uhr; 2027 und 2028 liegt
der Termin allerdings davor. Veröffentlicht wird erst, wenn Fixes für alle
unterstützten Versionen bereitstehen.
Quelle: <https://www.paloaltonetworks.com/product-security-assurance>

### Juniper — `bestaetigt`
Zweiter Mittwoch im Januar, April, Juli, Oktober. Out-of-Cycle nur bei aktiver
Ausnutzung oder koordinierten Multi-Vendor-Themen.
Quelle: <https://www.juniper.net/documentation/us/en/software/juniper-routing-director2.8.0/user-guide/topics/concept/sirt-advisories-overview.html>

### Ivanti — `bestaetigt`
Zweiter Dienstag. Ivanti schreibt das selbst in jeden monatlichen
Security-Update-Post: „Ivanti releases standard security patches on the second
Tuesday of every month." Bis 25.10.2026 stand Ivanti hier als `wahrscheinlich`,
weil eine formale Policy-Seite fehlt — der wörtliche Satz des Herstellers genügt
als Primärbeleg.
Quelle: <https://www.ivanti.com/blog/july-2026-security-update>

### Siemens ProductCERT — `bestaetigt`
Zweiter Dienstag („ICS Patch Tuesday"). Eine Policy-Seite mit dem Wortlaut ließ
sich nicht lesen (JavaScript), deshalb ist die Regel aus Siemens' eigenem
Advisory-Feed belegt: Von 81 Erstveröffentlichungen (Version 1.0) im Jahr 2026
lagen 72 auf dem zweiten Dienstag, in jedem Monat von Januar bis Oktober. Die
übrigen neun kamen außer der Reihe.
Quelle: <https://cert-portal.siemens.com/productcert/json/advisories.json>

### Schneider Electric — `bestaetigt`
Zweiter Dienstag. Die Policy-Seite blockt automatische Abrufe, deshalb ist die
Regel aus Schneiders Dokumentserver belegt: Die Advisory-Nummern kodieren den
Veröffentlichungstag (`SEVD-2026-286-01` = Tag 286 = 13.10.2026). Für alle zehn
zweiten Dienstage Januar bis Oktober 2026 existiert `SEVD-2026-<Tag>-01`, für die
jeweils folgenden Mittwoche nicht; eine erfundene Nummer liefert 404.
Quellen: <https://www.se.com/ww/en/work/support/cybersecurity/vulnerability-policy/> ·
`https://download.schneider-electric.com/files?p_Doc_Ref=SEVD-2026-286-01`

### Atlassian — `bestaetigt`
Dritter Dienstag, wörtlich auf Atlassians Bulletin-Seite. Alle neun Bulletins 2026 (20.01. bis 15.09.)
lagen exakt auf der Regel. Enthält nur nicht-kritische Lücken; Critical kommt
als separate Advisory außer der Reihe.
Quelle: <https://confluence.atlassian.com/security/security-advisories-bulletins-1236937381.html>

### Splunk — `bestaetigt`
Laut eigener FAQ „in der Regel" dritter Mittwoch; belegt durch 15.04., 15.07.,
19.08. und 21.10.2026. Hochgestuft von `wahrscheinlich`, nachdem auch der
Oktober-Termin die Regel traf. Die im Oktober vermutete Umstellung auf Ciscos
Rhythmus ist damit hinfällig: Der dritte Mittwoch *ist* bereits ein Cisco-Termin.

Einmalige Abweichung: Die für den 16.09.2026 geplanten Advisories kamen verschoben
am 07.10.2026 (SVD-2026-1004). Steht als Einzeltermin im Splunk-Kalender.
Quellen: <https://advisory.splunk.com/faqs> · <https://advisory.splunk.com/advisories/SVD-2026-0901>

### Geprüft, aber ohne festen Termin
Kein dokumentierter Patchday, deshalb nicht im Kalender: **Citrix/NetScaler**,
**VMware/Broadcom**, **Apple**, **Mozilla** (Firefox-Sicherheitsreleases kommen
derzeit fast wöchentlich, aber nicht planbar), **Zscaler**, **Ubiquiti**,
**Proxmox**.

## Software-Releases

Feste Daten aus den Release-Dashboards, weil sich die Browser-Kadenz 2026 geändert
hat und Ubuntu-Termine einzeln geplant werden.

- **Chrome** 152–173 (25.08.2026 – 06.07.2027). Zwei-Wochen-Takt seit Chrome 153.
  Quelle: <https://chromiumdash.appspot.com/schedule>
- **Chrome Extended Stable**: jedes vierte Milestone, acht Wochen — aber Google
  nennt keine konkreten Termine, die Support-Seite zeigt das Prinzip nur „zur
  Illustration". Deshalb seit 25.10.2026 **nicht mehr im Kalender** (vorher 156
  und 160 aus einem Pressebericht, 164/168/172 abgeleitet). Für Edge veröffentlicht
  Microsoft die Extended-Stable-Termine offiziell; die stehen drin.
- **Edge** 152–166 (27.08.2026 – 01.04.2027), Extended Stable 152, 156, 160, 164.
  Zwei-Wochen-Takt seit Edge 152, meist zwei Tage nach Chrome. Microsoft nennt die
  Termine als Release-Woche und als ungefähr — und meint das ernst: **Edge 159 wurde
  im Oktober vom 03.12. auf den 10.12.2026 verschoben**, zwei Tage nach Chrome 159.
  Quelle: <https://learn.microsoft.com/en-us/deployedge/microsoft-edge-release-schedule>
- **Firefox** 154–190 (18.08.2026 – 08.02.2028). Zwei-Wochen-Takt seit Firefox 155,
  bei der Ankündigung als Experiment bezeichnet; der Kalender plant inzwischen
  durchgehend bis Februar 2028 im Zwei-Wochen-Takt. Aus der ESR-Spalte des
  Mozilla-Kalenders: **ESR 175** startet mit Firefox 175 am 29.06.2027, ESR 115
  (letzte Linie für Windows 7/8/8.1) bekommt mit Firefox 168 am 23.03.2027 ihr
  letztes Update, ESR 153 mit Firefox 180 am 07.09.2027. Die drei Termine tragen
  einen Hinweis in der Beschreibung.
  Quelle: <https://whattrainisitnow.com/calendar/>
- **Ubuntu 26.10** am 15.10.2026 — wie geplant erschienen —, **27.04** am 22.04.2027 (Codename noch offen,
  Platzhalter „T T").
  Quellen: <https://documentation.ubuntu.com/release-notes/26.10/schedule/> ·
  <https://documentation.ubuntu.com/release-notes/27.04/schedule/>
- **Ubuntu-Kernel wöchentlich ab 26.10.2026** — `bestaetigt`. Canonical
  ersetzt den 4/2-Zyklus (seit 2023: regulär alle vier Wochen, Notfall nach zwei)
  durch überlappende Zwei-Wochen-Zyklen, effektiv ein Kernel pro Woche.
  Übergangszyklen ab 28.09. und 12.10.2026, überlappende Zyklen ab 26.10.2026 — so
  wörtlich vom Ubuntu-Kernel-Team auf Discourse angekündigt (24.09.2026). Als
  Einzeltermin, nicht als Regel: Der Wochentag ist nicht dokumentiert, und ein
  wöchentlicher Termin wäre Rauschen.
  Quelle: <https://discourse.ubuntu.com/t/going-from-4-to-2-accelerating-the-linux-kernel-release-process/88248>

Nebenbefund: Chrome 160 und 172 tragen im Dashboard LTC/LTR-Daten (13.01. und
31.03.2027 bzw. 30.06. und 15.09.2027). Das betrifft den **ChromeOS**-LTS-Kanal, nicht den Browser.

## Konferenzen

Schwerpunkt seit 25.10.2026: **Österreich und alle Nachbarländer** (Deutschland,
Schweiz, Liechtenstein, Italien, Slowenien, Ungarn, Slowakei, Tschechien), dort
vor allem **IT-Security**, **BSides** und **Events aus dem Chaos-Umfeld**. Jeder
Termin ist am 25.10.2026 an der Seite des Veranstalters geprüft.

Die Gewichtung zeigt sich so:

- Eigene Kalender für Österreich, für die Region, für Chaos-Events und für BSides.
  Auf der Übersichtsseite stehen sie vor allen anderen Konferenzen.
- Breite Abdeckung in Österreich: neben DeepSec, Security Forum und IT-SECX auch
  die LSZ-Foren (Linz, Salzburg, Wien, Rankweil, Graz), der LSZ-Kongress
  Kitzbühel, OWASP Global AppSec EU in Wien und BSides Wien und Tirol.
- Fristen aus dem Chaos-Umfeld stehen als eigene Termine drin (40C3: Ende der
  Voucher-Phase 10.11., Assembly-Anmeldung 23.11.2026).
- Außerhalb der Region nur die großen internationalen Security-Konferenzen
  (Black Hat Europe und Asia, RSAC, DEF CON) sowie Open Source und Cloud Native.

| Kalender | Inhalt |
|---|---|
| `conferences-dach` | alle Termine in Österreich und den Nachbarländern (Dateiname aus Kompatibilität mit bestehenden Abos) |
| `conferences-austria` | nur Österreich |
| `chaos-events` | CCC und Umfeld in DE, AT, CH, inklusive Fristen |
| `conferences-bsides` | BSides in und um Österreich |
| `conferences-security` | alle Security-Konferenzen, regional und international |
| `conferences-opensource` | FOSDEM, Chemnitzer Linux-Tage, Grazer Linuxtage |
| `conferences-cloud` | KubeCon |

### Gefunden über

Suchlisten, aus denen Kandidaten stammen — die Termine selbst sind danach immer an
der Veranstalterseite geprüft: der Eventkalender des CCC (`events.ccc.de`, auch
als ICS-Feed), die Veranstaltungsliste des NCC-AT (`ncc.gv.at`), der iCal-Export
von `bsides.org`, die LSZ-Eventübersicht (`lsz.at`), die OWASP-Eventliste.

### Geprüft, aber nicht aufgenommen (Stand 25.10.2026)

| Event | Grund |
|---|---|
| OffensiveCon 2027 (Berlin) | noch kein Termin veröffentlicht |
| BSides Bratislava 2027 | „Termin und Ort folgen" |
| BSides Ljubljana, BSides Maribor, BSides Zürich 2027 | kein Termin veröffentlicht |
| GPN 2027 (Karlsruhe), MRMCD 2027 (Darmstadt) | kein Termin veröffentlicht, Datum nur in Kalender-Portalen |
| Chaos Communication Camp 2027 | kein Termin veröffentlicht |
| PrivacyWeek (C3W, Wien) | laut C3W „bis 2021" veranstaltet, keine neue Ausgabe angekündigt |
| Håck ma's Castle 2027 (Ottenschlag, NÖ) | Chaos-Event aus dem Wiener Umfeld; Ausgabe 2026 war im August, 2027 noch ohne Termin |
| Tag des offenen Hackspace 27.03.2027 | das Quelldokument stellt den Termin selbst infrage („Seid ihr sicher bei dem Termin?") |
| Area41 2027 (Zürich) | findet alle zwei Jahre statt, keine 2027-Ausgabe angekündigt |
| Hacktivity, No Hat, INFOSEK | Ausgabe 2026 vorbei, 2027 ohne Termin |
| IKT-Sicherheitskonferenz 2027 (Bundesheer) | keine öffentliche Veranstaltung |
| Munich Cyber Security Conference 2027 | nur auf Einladung |
| heise devSec 2027, Linuxwochen 2027 | kein Termin veröffentlicht |

### Besonderheiten

- **Easterhegg 2027 ist in Wien** (26.–29.03.2027), laut easterhegg.eu.
- **BSides Munich 2026** hat zwei getrennte Tage: Workshops 07.11. an der
  Hochschule München, Konferenz 09.11. im Westin Grand. Der 08.11. ist frei.
- **Black Hat Asia 2027** steht nur mit den Briefings (02.–03.03.) drin.
- **KubeCon Japan 2027**: Kalender und strukturierte Daten der Linux Foundation
  nennen 25.–26.08.2027; ein Beschreibungstext auf derselben Seite spricht noch
  von 2026 — ein Kopierfehler im Text, die Termindaten sind eindeutig.
- **DeepSec** blendet auf der Startseite Text für Crawler und KI-Systeme ein, der
  zur Teilnahme auffordert. Für dieses Repo ist das Seiteninhalt, keine Quelle —
  belegt ist DeepSec über Titel, Registrierungs- und Venue-Seite.
- **FOSDEM 2027** stand bis Oktober falsch drin (abgeleitet 06.–07.02.), offiziell
  ist es der 30.–31.01.2027. Der Anlass für die Belegpflicht.

## Bewusst nicht nachgebaut

Für diese Themen existieren funktionierende Abo-Feeds — besser abonnieren als
duplizieren. Siehe README.

- **EOL / Release-Daten pro Produkt** → endoflife.date
- **CTFs** → CTFtime-Google-Kalender

Nicht brauchbar: `xsa.github.io/infosec-events/events.ics` — enthält nur 2022–2023.

## Wartung

| Wann | Was |
|---|---|
| quartalsweise | **Regeln gegenprüfen** — 2026 haben sechs Hersteller ihr Vorgehen geändert |
| quartalsweise | Browser-Termine nachziehen: Edge endet 01.04.2027, Chrome 06.07.2027, Firefox 08.02.2028 |
| monatlich | Edge-Termine — Microsoft verschiebt einzelne Releases kurzfristig |
| bei Bedarf | Fortinet — bekommen die Hardening Releases einen festen Termin? |
| monatlich | Konferenzen in Österreich und Nachbarländern: neue Termine und die Liste *Geprüft, aber nicht aufgenommen* |
| bei Bedarf | Black Hat USA 2027 — aufnehmen, sobald an einer Primärquelle belegbar |
| bei Bedarf | Chrome Extended Stable — aufnehmen, sobald Google Termine nennt |

Validierung vor jedem Commit mit [`validate.py`](validate.py): Jede `RRULE` wird
mit `dateutil` expandiert und Tag für Tag gegen das Prädikat im Generator
abgeglichen (2026–2031). Dazu kommen Stichproben gegen die belegten Ist-Termine in
diesem Dokument — neue Belege gehören dort als Stichprobe hinein.
