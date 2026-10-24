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

## Konfidenz-Stufen

Jedes Event trägt seine Stufe in der `DESCRIPTION`.

| Stufe | Bedeutung |
|---|---|
| `bestaetigt` | Primärquelle des Herstellers, oder die tatsächlichen Termine decken sich mit der Regel |
| `wahrscheinlich` | Sekundärquelle, plausibel und mehrfach übereinstimmend, nicht am Hersteller verifiziert |
| `abgeleitet` | Aus dem Muster geschlossen, nicht offiziell angekündigt |

Datumsbasierte Events unterhalb `bestaetigt` bekommen zusätzlich `STATUS:TENTATIVE`.

Mehrere Herstellerseiten (`oracle.com`, `blackhat.com`, `se.com`, `pressebox.de`)
liefern automatisierten Abrufen HTTP 403. Im Browser sind sie erreichbar; die
Termine sind dann über Sekundärquellen abgesichert, siehe die Einzelabschnitte.

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
Quelle: <https://msrc.microsoft.com/update-guide/releaseNote/>

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
Dritter Dienstag im Januar, April, Juli, Oktober.

Fußangel: Oracle formuliert die Regel historisch als *„Tuesday closest to the 17th"*.
Das ist **nicht** dasselbe — beginnt ein Monat an einem Mittwoch, liefert diese
Formulierung den zweiten Dienstag. Die angekündigten Termine (21.07.2026,
20.10.2026, 19.01.2027, 20.04.2027) folgen durchgängig dem dritten Dienstag.
Quelle: <https://www.oracle.com/security-alerts/>

### Oracle CSPU — `bestaetigt`
Seit Mai 2026 in allen acht Nicht-CPU-Monaten, dritter Dienstag.

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
dem ersten Montag. Bis Oktober 2026 zeigte der Kalender hier einen Tag zu früh.

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

### Ivanti — `wahrscheinlich`
Zweiter Dienstag. Ivantis monatliche Security-Update-Posts 2026 liegen alle auf dem
Patch Tuesday; eine formale Policy-Seite war nicht abrufbar.
Quelle: <https://www.ivanti.com/blog/september-2026-security-update>

### Siemens ProductCERT — `wahrscheinlich` · Schneider Electric — `bestaetigt`
Beide am zweiten Dienstag („ICS Patch Tuesday"). Für Schneider steht die Regel in
der eigenen Vulnerability Policy; für Siemens ist sie über die monatliche
SecurityWeek-Berichterstattung belegt, die Siemens-Seite selbst nicht geprüft.
Quellen: <https://www.se.com/ww/en/work/support/cybersecurity/vulnerability-policy/> ·
<https://www.securityweek.com/ics-patch-tuesday-security-advisories-released-by-siemens-schneider-cisa-others/>

### Atlassian — `bestaetigt`
Dritter Dienstag. Alle neun Bulletins 2026 (20.01. bis 15.09.)
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
- **Chrome Extended Stable**: jedes vierte Milestone, acht Wochen. Google nennt
  keine konkreten Termine, die Support-Seite zeigt das Prinzip nur „zur
  Illustration". 156 → 160 ist von 9to5Google berichtet (`wahrscheinlich`),
  164, 168 und 172 sind daraus abgeleitet (`abgeleitet`). Microsoft bestätigt für Edge
  offiziell dasselbe Muster (152, 156, 160, 164).
  Quelle: <https://support.google.com/chrome/a/answer/16942104>
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
- **Ubuntu-Kernel wöchentlich ab 26.10.2026** — `wahrscheinlich`. Canonical
  ersetzt den 4/2-Zyklus (seit 2023: regulär alle vier Wochen, Notfall nach zwei)
  durch überlappende Zwei-Wochen-Zyklen, effektiv ein Kernel pro Woche.
  Übergangszyklen ab 28.09. und 12.10.2026. Canonicals eigener Blogpost nennt keine
  Daten; die stammen aus The Register und OMG! Ubuntu, die sich auf Ubuntu Discourse
  beziehen. Als Einzeltermin, nicht als Regel: Der Wochentag ist nicht
  dokumentiert, und ein wöchentlicher Termin wäre Rauschen.
  Quellen: <https://canonical.com/blog/accelerating-delivery-of-cve-fixes-with-a-new-kernel-release-strategy> ·
  <https://www.theregister.com/os-platforms/2026/09/24/cve-flood-pushes-ubuntu-onto-weekly-kernel-release-cycle/5298912>

Nebenbefund: Chrome 160 und 172 tragen im Dashboard LTC/LTR-Daten (13.01. und
31.03.2027 bzw. 30.06. und 15.09.2027). Das betrifft den **ChromeOS**-LTS-Kanal, nicht den Browser.

## Konferenzen

Kuratiert, **nicht vollständig**. Dreizehn Security- und vier Cloud-Native-Termine,
davon sieben im DACH-Raum (eigener Kalender).

Neu am 25.10.2026: Black Hat Asia 2027 (28.02.–03.03., Marina Bay Sands,
`wahrscheinlich`) und KubeCon Japan 2027 (25.–26.08., Yokohama, Linux-Foundation-
Kalender). Noch ohne bestätigte Termine und deshalb nicht drin: OffensiveCon 2027,
BSides Vienna 2027, IT-SECX 2027, Chaos Communication Camp 2027.

**Korrektur FOSDEM 2027:** Bis Oktober stand FOSDEM hier als `abgeleitet` auf dem
06.–07.02.2027 („erstes Februar-Wochenende"). Das war falsch. Offiziell
angekündigt am 30.08.2026: **30.–31.01.2027**. FOSDEM liegt je nach Jahr am letzten
Januar- oder ersten Februar-Wochenende (2025: 01.–02.02., 2026: 31.01.–01.02.),
eine einfache Regel gibt es nicht. Konsequenz: Konferenztermine werden hier nicht
mehr abgeleitet, nur noch belegt oder weggelassen.

Hochgestuft auf `bestaetigt`: 40C3 (CCC-Ankündigung, Motto „Model Citizens",
Hamburg Messe), RSAC 2027 (Moscone-Veranstaltungskalender), TROOPERS27
(troopers.de, Trainings 21.–22.06., Konferenz 23.–25.06.).

Neu: DeepSec 2026 (Wien), Security Forum Hagenberg 2027, secIT 2027, it-sa 2027,
Black Hat Europe 2026, KubeCon North America 2026.

Weiterhin `wahrscheinlich`: Black Hat USA 2027, Black Hat Europe 2026 und Black Hat
Asia 2027 (blackhat.com blockiert automatisierte Abrufe), secIT 2027 (nur Messekalender).

## Bewusst nicht nachgebaut

Für diese Themen existieren funktionierende Abo-Feeds — besser abonnieren als
duplizieren. Siehe README.

- **EOL / Release-Daten pro Produkt** → endoflife.date
- **CTFs** → CTFtime-Google-Kalender

Nicht brauchbar: `xsa.github.io/infosec-events/events.ics` — enthält nur 2022–2023.

## Wartung

| Wann | Was |
|---|---|
| quartalsweise | **Regeln gegenprüfen** — 2026 haben fünf Hersteller ihren Rhythmus geändert |
| quartalsweise | Browser-Termine nachziehen: Edge endet 01.04.2027, Chrome 06.07.2027, Firefox 08.02.2028 |
| monatlich | Edge-Termine — Microsoft verschiebt einzelne Releases kurzfristig |
| bei Bedarf | Fortinet — bekommen die Hardening Releases einen festen Termin? |
| bei Bedarf | Chrome Extended Stable — sobald Google Termine nennt, `abgeleitet` hochstufen |
| jährlich | Konferenztermine des Folgejahres belegen |

Validierung vor jedem Commit mit [`validate.py`](validate.py): Jede `RRULE` wird
mit `dateutil` expandiert und Tag für Tag gegen das Prädikat im Generator
abgeglichen (2026–2031). Dazu kommen Stichproben gegen die belegten Ist-Termine in
diesem Dokument — neue Belege gehören dort als Stichprobe hinein.
