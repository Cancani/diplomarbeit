# Diplomarbeit: Agentenbasierte Hybrid-Cloud-Bereitstellung von Lernumgebungen mit Kubernetes, KubeVirt und MCP

!!! info "Lesehinweis"
    Diese Dokumentation entsteht laufend während der Projektlaufzeit vom 14.09.2026 bis 18.12.2026. Sie ist sequentiell lesbar aufgebaut: Kapitel 1 ordnet das Problem ein, Kapitel 2 beschreibt, wie das Projekt geführt wird, die Kapitel 3 bis 7 folgen dem fachlichen Weg von der Analyse über die Umsetzung bis zur Bewertung, die Kapitel 8 bis 10 schliessen die Arbeit ab. Wöchentliche Statusberichte und das Projektjournal liegen in eigenen Bereichen und werden aus Kapitel 2 heraus verlinkt.

| | |
| --- | --- |
| Diplomand | Efekan Demirci, ITCNE24, TBZ Höhere Fachschule |
| Auftraggeber | Technische Berufsschule Zürich, Informatikdienst |
| Firmenexperte | Kuno Vogt, Leiter Informatikdienst TBZ |
| Schulexperte | Thanam Pangri, HF-Lehrgangsleitung |
| Laufzeit | 14.09.2026 bis 18.12.2026 |
| Version | 0.1, Projektstart |
| Grundlage | Bewilligte Projektbeschreibung vom 10.09.2026, Merkblatt A Stand Juni 2026 |

---

## Management Summary

> Wird am Projektende verfasst und zusätzlich als separates Dokument mit unterschriebenem Ehrenwort abgegeben. Grundlage ist das Management Summary aus der bewilligten Projektbeschreibung vom 10.09.2026.

---

## 1 Einleitung

### 1.1 Ausgangslage

Die Technische Berufsschule Zürich stellt für den Unterricht digitale Übungsumgebungen bereit, in denen Lernende praktische technische Aufgaben durchführen. Diese Lernumgebungen werden heute auf einer lokalen Plattform mit MAAS, LernMAAS, Konfigurationsdateien und Shellskripten bereitgestellt. Das Verfahren ist im Betrieb etabliert und bleibt während der gesamten Diplomarbeit unverändert verfügbar.

Die fachliche Beschreibung einer Lernumgebung und ihre technische Bereitstellung sind dabei eng mit dieser Plattform verbunden. Soll dieselbe Lernumgebung auf einer anderen Infrastruktur entstehen, müssen Abläufe, Schnittstellen und Skripte separat angepasst oder neu entwickelt werden. Daraus ergeben sich zusätzlicher manueller Aufwand, eine stärkere Abhängigkeit von spezifischem Wissen einzelner Personen und eine eingeschränkte Wiederverwendbarkeit der bestehenden Beschreibungen.

> Die detaillierte IST-Analyse folgt aus Sprint 1, User Story US07. Sie ergänzt diesen Abschnitt um den konkreten Ablauf, die beteiligten Komponenten und die manuellen Schritte des heutigen Vorgehens.

### 1.2 Problemstellung

Es fehlt ein einheitliches Modell, mit dem eine Lernumgebung unabhängig von der gewählten Plattform beschrieben und über einen gemeinsamen Ablauf verwaltet werden kann. Ohne ein solches Modell bleibt die fachliche Beschreibung an eine einzelne technische Umsetzung gebunden.

Vor einer möglichen späteren Weiterentwicklung der lokalen Lernplattform soll deshalb geklärt werden, ob ein plattformübergreifender Ansatz technisch machbar ist und gegenüber dem heutigen Vorgehen einen nachvollziehbaren Mehrwert bietet.

### 1.3 Zielbild

Eine Lernumgebung wird einmal fachlich beschrieben und über denselben Lebenszyklus entweder lokal oder in der Public Cloud verwaltet. Die Bedienlogik bleibt auf beiden Zielplattformen gleich, während die plattformspezifische Umsetzung davon getrennt ist. Der Ablauf soll reproduzierbar und messbar sein und ohne manuelle technische Entscheidungen auskommen.

Der Proof of Concept liefert damit eine Entscheidungsgrundlage für eine mögliche spätere Weiterentwicklung, ohne die bestehende produktive Umgebung zu verändern.

### 1.4 Zielsetzungen und Erfolgskriterien

Die fünf Teilziele aus der bewilligten Projektbeschreibung werden als SMART-Ziele mit prüfbaren Erfolgskriterien geführt. Jedes Ziel wird in jedem Sprint Review gegen diese Tabelle abgeglichen, die Spalte Status wird dabei nachgeführt.

| ID | Ziel | Messkriterium | Zielwert | Nachweis | Status |
| --- | --- | --- | --- | --- | --- |
| Z1 | Plattformneutrales Modell für Lernumgebungen | Versioniertes YAML-Modell mit JSON-Schema, gültige Definition wird akzeptiert, ungültige abgewiesen | 1 Modell, 1 Schema, je 1 positiver und 1 negativer Testfall bestehen | Repository, Testprotokoll | Offen |
| Z2 | Zentraler Agent mit Zustandsführung | create, status, reset und delete laufen über festgelegte Zustandsübergänge, Zustand ist persistent | 4 Operationen funktionsfähig, reset erzeugt aus derselben Definition neu | Quellcode, Zustandsdiagramm, Testprotokoll | Offen |
| Z3 | On-Prem-Backend mit Kubernetes und KubeVirt | Test-Lernumgebung wird automatisiert bereitgestellt und vollständig entfernt | 3 vollständige Durchläufe ohne manuelle Korrektur | Laufprotokolle, Screenshots | Offen |
| Z4 | Bewertung der MCP-basierten Adapterarchitektur | Dieselbe Definition läuft lokal und auf genau einer Public Cloud, Bewertung gegen direkte API-Anbindung | 3 vollständige Durchläufe in der Cloud, Bewertung nach 5 Kriterien dokumentiert | Laufprotokolle, Bewertungstabelle | Offen |
| Z5 | Messbarer Vergleich mit dem heutigen Vorgehen | Bereitstellungszeit, manuelle Eingriffe, Reproduzierbarkeit, vollständiger Abbau | Vorher- und Nachher-Werte für denselben Testfall protokolliert | Messprotokoll, Vergleichstabelle | Offen |

Die Ziele Z1 bis Z3 beschreiben die zu erstellenden Bestandteile, Z4 und Z5 beziehen sich auf deren Beurteilung. Damit ist zu jedem Zeitpunkt des Projekts ersichtlich, welche Ziele bereits nachgewiesen sind und welche noch offen sind.

### 1.5 Erfolgskriterien des Proof of Concept

Der Proof of Concept gilt als erfolgreich, wenn die folgenden Kriterien des verbindlichen Kernumfangs nachgewiesen sind. Sie stammen unverändert aus der bewilligten Projektbeschreibung und bilden zugleich die projektweite Definition of Done.

- [ ] Das YAML-Modell und das zugehörige JSON-Schema sind versioniert. Das Modell deckt die ausgewählten Konfigurationsmerkmale der LernMAAS-Profile m239, m254 und m426 ab. Eine gültige Definition wird akzeptiert, eine bewusst ungültige wird abgewiesen, und die technisch reduzierte Test-Lernumgebung ist festgelegt.
- [ ] Der Agent validiert die Definition, speichert den Zustand persistent und führt create, status, reset und delete über festgelegte Zustandsübergänge aus. reset löscht die Umgebung und erstellt sie aus derselben Definition neu.
- [ ] Die gemeinsame Definition wird über die MCP-basierten Adapter lokal auf einem Kubernetes-Cluster mit KubeVirt und auf genau einer Public-Cloud-Plattform bereitgestellt. Auf beiden Zielplattformen erreicht die VM den festgelegten Zustand und der definierte Testdienst besteht den Readiness-Check.
- [ ] Auf jeder Zielplattform werden drei aufeinanderfolgende vollständige Durchläufe durchgeführt, insgesamt sechs. Alle Durchläufe funktionieren ohne manuelle Korrektur.
- [ ] Nach jedem delete sind keine dem Testlauf zugeordneten Ressourcen mehr vorhanden.
- [ ] Bereitstellungszeit und manuelle Eingriffe sind für das heutige Vorgehen und den Proof of Concept protokolliert. Der Vorher-Nachher-Vergleich sowie die Bewertung der MCP-basierten Architektur gegenüber einer direkten API-Anbindung sind dokumentiert.
- [ ] Die gewonnenen Erkenntnisse und die erarbeiteten technischen Komponenten sind hinsichtlich ihrer Übertragbarkeit auf eine mögliche zukünftige produktive Umgebung beurteilt und dokumentiert.

### 1.6 Abgrenzung

Der Umfang ist bewusst so festgelegt, dass der vollständige und messbare Nachweis innerhalb der verfügbaren Projektzeit möglich bleibt. Nicht Teil dieser Arbeit sind:

| Nicht im Umfang | Begründung |
| --- | --- |
| Migration oder Abschaltung der bestehenden MAAS-Umgebung | Die produktive Umgebung bleibt unverändert in Betrieb und dient als Vergleichsbasis |
| Produktiver Betrieb der neuen Infrastruktur | Der Nachweis erfolgt als Proof of Concept, nicht als Einführung |
| Vollständige Umsetzung aller Unterrichtsmodule | Eine technisch reduzierte Test-Lernumgebung genügt für den Nachweis des Lebenszyklus |
| Sprachmodellbasierte Entscheidungslogik | Der Agent arbeitet nach festgelegten Regeln, weil nur so reproduzierbare Ergebnisse entstehen |
| Bedienoberfläche | Der Nachweis erfolgt über die Kommandozeile, eine Oberfläche liefert für die Fragestellung keinen zusätzlichen Erkenntnisgewinn |
| Zweite Public Cloud | Eine Plattform genügt, um die Austauschbarkeit über die Adapterschicht zu zeigen |
| GitOps oder Argo CD | War Gegenstand der Semesterarbeit 5 und wird in dieser Arbeit nicht erneut behandelt |
| Hochverfügbarkeit, verteilter Storage, produktive Skalierung | Betriebsthemen, die erst bei einer produktiven Einführung relevant werden |
| Hardwarebeschaffung und betriebliche Netzwerkumstellungen | Es wird ausschliesslich vorhandene, freigegebene Hardware verwendet |

Diese Punkte werden im Ausblick in Kapitel 10 behandelt.

### 1.7 Zielgruppe und Lesehinweise

Die Dokumentation richtet sich an die beiden Experten, an den Informatikdienst der TBZ und an die HF-Lehrgangsleitung. Sie ist so geschrieben, dass ein fachlich versierter Leser ohne Vorwissen über die TBZ-Umgebung folgen kann. Fachbegriffe werden beim ersten Vorkommen kurz erläutert und zusätzlich im Glossar am Ende der Arbeit erklärt.

### 1.8 Themenfeldabdeckung

Die Diplomarbeit deckt mehrere Themenfelder des Lehrgangs ab. Die folgende Tabelle ordnet jedem Themenfeld den konkreten Bezug in dieser Arbeit und die Kapitel zu, in denen das Ergebnis nachvollziehbar ist.

| Themenfeld | Bezug in dieser Arbeit | Kapitel |
| --- | --- | --- |
| Cloud Engineering | Entwurf und Beurteilung einer Lösung für lokale und Public-Cloud-Infrastruktur | 3, 4, 6 |
| DevOps und Automatisierung | Reproduzierbare Bereitstellung, Zustandsführung, Tests, vollständiger Abbau | 4, 5 |
| Cloud-native Virtualisierung | Betrieb virtueller Maschinen auf Kubernetes mit KubeVirt | 4 |
| Schnittstellen- und Architekturdesign | Trennung zwischen Fachmodell, zentraler Steuerung und plattformspezifischen Adaptern | 3, 4 |
| Projektmanagement | Hybrides Vorgehen mit Sprints innerhalb fixer Meilensteine | 2 |
| Wirtschaftlichkeit | Kosten-Nutzen-Betrachtung auf Basis erhobener Messwerte | 6 |
| Betrieb und Schulung | Runbook und Einführung für Nutzende | 7 |

Der Schwerpunkt liegt auf Cloud Engineering, Automatisierung und Architekturdesign. Projektmanagement und Wirtschaftlichkeit werden in eigenen Kapiteln geführt, damit die fachlichen Kapitel den technischen Ablauf zusammenhängend darstellen können.

---
## 2 Projektmanagement

### 2.1 Vorgehensmodell

#### 2.1.1 Das magische Dreieck als Ausgangspunkt

Von den drei Grössen Leistung, Zeit und Kosten sind zwei von aussen vorgegeben und stehen damit nicht zur Steuerung zur Verfügung.

| Dimension | Status | Begründung |
| --- | --- | --- |
| Zeit | Fix | Abgabe am 18.12.2026, Termine aus Merkblatt A, keine Verschiebung möglich |
| Kosten | Fix | Vorhandene Hardware der TBZ, maximal CHF 50 Cloud-Guthaben des Diplomanden, keine Beschaffung |
| Leistung | Variabel | Der Funktionsumfang ist die einzige echte Stellgrösse |

Daraus ergibt sich die Steuerungsregel dieses Projekts: Bei Abweichungen wird der Umfang reduziert, der Termin wird nicht verschoben und die Qualität wird nicht gesenkt. In welcher Reihenfolge reduziert wird, ist über die MoSCoW-Priorisierung in Kapitel 2.10 vorab festgelegt, damit dieser Entscheid nicht erst unter Zeitdruck fällt.

#### 2.1.2 Wahl des Vorgehensmodells

Massgebend für die Wahl waren die Klarheit der Anforderungen, die technische Unsicherheit, die vorgegebenen Termine, die Teamgrösse und die geforderte Nachweisführung.

| Kriterium | Klassisch phasenorientiert | Rein agil nach Scrum | Gewählt: hybrid |
| --- | --- | --- | --- |
| Anforderungsklarheit | Setzt stabile Anforderungen voraus | Erlaubt Lernen während der Umsetzung | Ziele und Erfolgskriterien sind durch die bewilligte Projektbeschreibung fix, der Lösungsweg ist offen |
| Technische Unsicherheit | Hoch riskant bei neuer Technologie | Kurze Feedbackschleifen federn Unsicherheit ab | KubeVirt und MCP sind für den Diplomanden neu, iteratives Vorgehen ist nötig |
| Termine | Meilensteine klar planbar | Sprintenden sind flexibel | Die Zwischenpräsentationen sind fixe Meilensteine, die Sprints richten sich danach |
| Teamgrösse | Rollen setzen ein Team voraus | Rollen setzen ein Team voraus | Einzelprojekt, die Rollen werden angepasst |
| Nachweisführung | Phasenfreigaben | Increment und Review | Beides kombiniert |

Gewählt wird ein hybrides Vorgehen. Die äussere Struktur ist phasenorientiert und folgt den fixen Meilensteinen aus Merkblatt A, innerhalb dieser Struktur wird in drei Sprints iterativ gearbeitet.

#### 2.1.3 Angewandte Scrum-Elemente und bewusste Abweichungen

Scrum ist für ein Team von drei bis neun Personen konzipiert, diese Arbeit ist ein Einzelprojekt. Die Elemente werden deshalb in angepasster Form übernommen, angepasst sind vor allem die Rollen und das Daily Scrum.

| Scrum-Element | Anwendung in dieser Arbeit | Abweichung und Begründung |
| --- | --- | --- |
| Product Owner | Der Firmenexperte nimmt die Priorisierungsrolle wahr, der Diplomand schlägt vor | Keine tägliche Verfügbarkeit, Abstimmung an den Reviews und bei Bedarf im Teams-Kanal |
| Scrum Master | Entfällt als eigene Rolle | Der Diplomand moderiert seinen eigenen Prozess, die Retrospektive ersetzt die externe Prozessbeobachtung |
| Development Team | Der Diplomand allein | Einzelprojekt gemäss Merkblatt A, die Arbeit muss selbständig durchgeführt werden |
| Product Backlog | Vollständig geführt als GitHub Issues, siehe Kapitel 2.8 | Keine |
| Sprint Backlog | Sprintzuordnung im Project Board über das Feld Sprint und über Milestones | Keine |
| Sprint Planning | Zu Sprintbeginn, Ergebnis ist ein dokumentiertes Sprintziel mit Story-Point-Budget | Keine |
| Daily Scrum | Ersetzt durch einen Journaleintrag pro Arbeitseinheit | Ein tägliches Abstimmungstreffen setzt mehrere Beteiligte voraus, der Journaleintrag erfüllt denselben Zweck der Transparenz |
| Sprint Review | Die Zwischenpräsentationen mit den Experten sind die Sprint Reviews | Keine, dies ist in der Projektbeschreibung so vereinbart |
| Sprint Retrospektive | Nach jedem Sprint mit dem Starfish-Modell | Keine |
| Increment | Am Ende jedes Sprints existiert ein demonstrierbarer Stand | Keine |
| Velocity | Wird pro Sprint erhoben und für die Planung des Folgesprints verwendet | Basiswert aus der Erstschätzung, ab Sprint 2 aus Ist-Werten |

### 2.2 Projektorganisation und Rollen

Die Projektorganisation umfasst vier Beteiligte.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 400" width="720" height="400" role="img" aria-label="Projektorganisation mit vier Beteiligten" class="dia-svg"><style>.dia-svg text{font-family:IBM Plex Sans,system-ui,sans-serif;fill:var(--md-default-fg-color,#1a1a1a)}.dia-svg .k{font-size:14px}.dia-svg .kb{font-size:15px;font-weight:600}.dia-svg rect{fill:var(--md-default-bg-color,#fff);stroke:var(--md-default-fg-color--lighter,#bbb)}.dia-svg rect.w{fill:var(--md-code-bg-color,#f2f2f2)}.dia-svg path{fill:none;stroke:var(--md-default-fg-color--lighter,#bbb);stroke-width:1.3}</style><defs><marker id="sp" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--md-default-fg-color--lighter,#bbb)" stroke="none"/></marker></defs><path d="M 170.0 82 L 170.0 116.0 L 170.0 116.0 L 170.0 143" marker-end="url(#sp)"/><path d="M 550.0 82 L 550.0 116.0 L 550.0 116.0 L 550.0 143" marker-end="url(#sp)"/><path d="M 170.0 212 L 170.0 256.0 L 360.0 256.0 L 360.0 293" marker-end="url(#sp)"/><path d="M 550.0 212 L 550.0 256.0 L 360.0 256.0 L 360.0 293" marker-end="url(#sp)"/><rect class="" x="20" y="20" width="300" height="62" rx="6"/><text class="kb" x="170.0" y="46" text-anchor="middle">Auftraggeber</text><text class="k" x="170.0" y="66" text-anchor="middle">TBZ Informatikdienst</text><rect class="" x="400" y="20" width="300" height="62" rx="6"/><text class="kb" x="550.0" y="46" text-anchor="middle">HF-Lehrgangsleitung</text><text class="k" x="550.0" y="66" text-anchor="middle">TBZ Weiterbildung</text><rect class="" x="20" y="150" width="300" height="62" rx="6"/><text class="kb" x="170.0" y="176" text-anchor="middle">Firmenexperte</text><text class="k" x="170.0" y="196" text-anchor="middle">Kuno Vogt</text><rect class="" x="400" y="150" width="300" height="62" rx="6"/><text class="kb" x="550.0" y="176" text-anchor="middle">Schulexperte</text><text class="k" x="550.0" y="196" text-anchor="middle">Thanam Pangri</text><rect class="w" x="210" y="300" width="300" height="62" rx="6"/><text class="kb" x="360.0" y="326" text-anchor="middle">Diplomand und Projektleiter</text><text class="k" x="360.0" y="346" text-anchor="middle">Efekan Demirci</text></svg>

**RACI-Matrix**

Die Verantwortlichkeiten sind je Aufgabe mit einer RACI-Matrix zugeordnet. R steht für durchführend, A für rechenschaftspflichtig, C für konsultiert und I für informiert.

| Aufgabe | Diplomand | Firmenexperte | Schulexperte | Auftraggeber |
| --- | --- | --- | --- | --- |
| Projektplanung und Steuerung | R, A | C | C | I |
| Priorisierung des Backlogs | R | A | C | I |
| Technische Entscheide und Architektur | R, A | C | C | I |
| Umsetzung und Tests | R, A | I | I | I |
| Änderung von Zielen oder Fokus | R | A | A | C |
| Freigabe der Sprintergebnisse | R | A | A | I |
| Bewertung der Arbeit | I | R, A | R, A | I |
| Bereitstellung von Hardware und Zugängen | C | C | I | A |
| Dokumentation und Abgabe | R, A | I | I | I |

In der Zeile Änderung von Zielen oder Fokus ist A zweimal vergeben. Das ist beabsichtigt, weil Merkblatt A für grössere Projektänderungen die Zustimmung beider Experten verlangt. Der zugehörige Prozess ist in Kapitel 2.14 beschrieben.

**Deklaration von Abhängigkeiten**

Merkblatt A verlangt die Deklaration von Abhängigkeiten und Verbindungen zwischen Diplomand und Experten, auch ausserhalb der Arbeitszeit.

| Beziehung | Art | Umgang |
| --- | --- | --- |
| Diplomand und Kuno Vogt | Direktes Vorgesetztenverhältnis im Informatikdienst der TBZ | Offengelegt. Die Bewertung erfolgt gemeinsam mit dem Schulexperten, technische Entscheide und Umsetzung liegen beim Diplomanden |
| Diplomand und Thanam Pangri | Ausschliesslich schulisches Verhältnis als Dozent und Lehrgangsleitung | Keine besondere Massnahme nötig |
| Ausserhalb der Arbeitszeit | Keine Verbindungen zwischen Diplomand und Experten | Keine |

Die Offenlegung des Vorgesetztenverhältnisses erfolgte beim Kickoff gegenüber beiden Experten. Weitere Abhängigkeiten bestehen nicht.

### 2.3 Stakeholder

#### Stakeholderliste

Vier Gruppen sind vom Projekt betroffen oder beeinflussen seinen Verlauf.

| Stakeholder | Vertreten durch | Rolle im Projekt | Interesse | Einfluss | Erwartung | Mögliche Konfliktlinie |
| --- | --- | --- | --- | --- | --- | --- |
| HF-Weiterbildung TBZ | Thanam Pangri, HF-Lehrgangsleitung | Schulexperte, Bewertung, Eigentümer der Lernumgebungen | Hoch | Hoch | Methodisch sauberes Vorgehen, nachvollziehbare Dokumentation, klar herausgearbeiteter Mehrwert von MCP | Technische Tiefe gegen methodische Vollständigkeit |
| Informatikdienst TBZ | Kuno Vogt, Leiter Informatikdienst | Firmenexperte, Auftraggebervertreter, direkter Vorgesetzter, betroffen durch die Nutzung der Hardware im HF-Labor | Hoch | Hoch | Belastbare Entscheidungsgrundlage, kein Eingriff in den produktiven Betrieb | Die Projektarbeit darf das Tagesgeschäft nicht belasten |
| Dozierende HF | Dozierende der Module m239, m254 und m426 | Fachliche Auskunft, spätere Nutzende | Mittel | Niedrig | Lernumgebungen müssen fachlich das Gleiche leisten wie heute | Eine reduzierte Test-Lernumgebung könnte als Abwertung ihrer Module gelesen werden |
| Lernende der TBZ | | Endnutzende der Lernumgebungen | Niedrig | Niedrig | Funktionierende Übungsumgebungen | Keine, das bestehende System bleibt unverändert in Betrieb |

Die Dozierenden und die Lernenden sind vom Proof of Concept nicht unmittelbar betroffen, da die bestehende Lernplattform während der gesamten Laufzeit weiterbetrieben wird.

#### Einfluss-Interesse-Portfolio

Die Einordnung nach Einfluss und Interesse bildet die Grundlage für die Umgangsstrategie.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 780 540" width="780" height="540" role="img" aria-label="Stakeholder nach Einfluss und Interesse" class="dia-svg"><style>.dia-svg text{font-family:IBM Plex Sans,system-ui,sans-serif;fill:var(--md-default-fg-color,#1a1a1a)}.dia-svg .kb{font-size:15px;font-weight:600}.dia-svg .ax{font-size:13px;fill:var(--md-default-fg-color--light,#666)}.dia-svg .qt{font-size:13px;font-weight:600;fill:var(--md-default-fg-color--light,#888)}.dia-svg rect{fill:none;stroke:var(--md-default-fg-color--lighter,#bbb)}.dia-svg rect.f{fill:var(--md-code-bg-color,#f4f4f4);stroke:none}.dia-svg line{stroke:var(--md-default-fg-color--lighter,#bbb);stroke-width:1}.dia-svg circle{fill:var(--md-default-fg-color,#1a1a1a)}</style><rect class="f" x="450.0" y="64.0" width="280.0" height="200.0"/><rect x="170" y="64" width="560" height="400" rx="4"/><line x1="450.0" y1="64" x2="450.0" y2="464"/><line x1="170" y1="264.0" x2="730" y2="264.0"/><text class="qt" x="186.8" y="248.0">Zufrieden halten</text><text class="qt" x="466.8" y="248.0">Eng einbinden</text><text class="qt" x="186.8" y="448.0">Beobachten</text><text class="qt" x="466.8" y="448.0">Informiert halten</text><circle cx="662.8" cy="96.0" r="6"/><text class="kb" x="649.8" y="101.0" text-anchor="end">HF-Weiterbildung</text><circle cx="629.2" cy="152.0" r="6"/><text class="kb" x="616.2" y="157.0" text-anchor="end">Informatikdienst TBZ</text><circle cx="517.2" cy="352.0" r="6"/><text class="kb" x="530.2" y="357.0">Dozierende HF</text><circle cx="338.0" cy="404.0" r="6"/><text class="kb" x="351.0" y="409.0">Lernende</text><text class="ax" x="170" y="490">geringes Interesse</text><text class="ax" x="730" y="490" text-anchor="end">hohes Interesse</text><text class="ax" x="152" y="464" text-anchor="start" transform="rotate(-90 152 464)">geringer Einfluss</text><text class="ax" x="152" y="64" text-anchor="end" transform="rotate(-90 152 64)">hoher Einfluss</text><text class="kb" x="170" y="40">Stakeholder nach Einfluss und Interesse</text></svg>

#### Abgeleitete Umgangsstrategie

Aus der Einordnung im Portfolio ergibt sich je Quadrant eine Strategie und eine konkrete Massnahme.

| Gruppe | Strategie | Konkrete Massnahme |
| --- | --- | --- |
| Eng einbinden: HF-Weiterbildung, Informatikdienst TBZ | Aktiv einbeziehen, Entscheide gemeinsam absichern | Drei Zwischenpräsentationen als Sprint Reviews, wöchentlicher Statusbericht, Change Requests mit Zustimmung beider Experten. Die Abgrenzung des Umfangs wird beim Kickoff ausdrücklich bestätigt. Die Nutzung der Hardware im HF-Labor wird vorab angekündigt |
| Informiert halten: Dozierende HF | Fachlich konsultieren, Erwartungen klären | Bei der Ableitung der Test-Lernumgebung in US08 konsultieren, Abgrenzung des Proof of Concept aktiv erklären |
| Beobachten: Lernende | Keine aktive Kommunikation nötig | Das bestehende System bleibt während der gesamten Laufzeit unverändert in Betrieb |

#### Eskalationsweg

Bleibt eine Entscheidung oder eine benötigte Zuarbeit aus, wird der folgende Weg eingehalten. Er ist vorab festgelegt, damit im Ereignisfall keine Zeit für die Abstimmung des Vorgehens verloren geht.

1. Fachliche oder organisatorische Blockade wird erkannt und im Journal festgehalten
2. Innerhalb von 24 Stunden Information an den Firmenexperten über den Teams-Kanal, bei Dringlichkeit telefonisch
3. Bleibt eine Antwort länger als zwei Arbeitstage aus, wird der Schulexperte einbezogen
4. Bei Blockaden mit Auswirkung auf einen Meilenstein wird die Ampel im Statusbericht auf Rot gesetzt und eine Umfangsreduktion vorgeschlagen

### 2.4 Kommunikationsplan

Der Kommunikationsplan legt fest, welche Information welchen Empfänger zu welchem Zeitpunkt über welchen Kanal erreicht. Er ist so angelegt, dass die Experten den Projektstand jederzeit ohne Rückfrage einsehen können.

| Was | An wen | Wann | Kanal | Zweck |
| --- | --- | --- | --- | --- |
| Wöchentlicher Statusbericht | Beide Experten | Jeden Freitag bis 18:00 | Markdown im Repository, veröffentlicht über GitHub Pages, zusätzlich kurzer Post mit Link im Teams-Kanal | Fortschritt, Abweichungen, nächste Schritte |
| Projektjournal | Jederzeit einsehbar | Laufend, mindestens pro Arbeitseinheit | Repository und GitHub Pages | Nachvollziehbarkeit von Ereignissen und Entscheiden |
| Einladung zu Meilensteinen | Beide Experten | Mindestens 10 Arbeitstage vorher | Outlook-Termin mit Teams-Link | Terminsicherung |
| Zwischenpräsentation und Sprint Review | Beide Experten | Wochen vom 19.10., 16.11. und 14.12.2026 | Online-Meeting, Präsentation und Demo | Abnahme des Sprintergebnisses, Steuerungsfeedback |
| Change Request | Beide Experten | Bei Bedarf, spätestens 5 Arbeitstage vor Wirksamkeit | Teams-Kanal, dokumentiert in Kapitel 2.14 | Zustimmung zu Änderungen an Zielen oder Fokus |
| Kurze Fachfrage | Firmenexperte | Bei Bedarf | Teams-Chat | Klärung, Antwort innerhalb von zwei Arbeitstagen erwartet |
| Eskalation bei Blockade | Firmenexperte, bei Ausbleiben Schulexperte | Innerhalb von 24 Stunden nach Erkennen | Teams-Chat, bei Dringlichkeit Telefon | Auflösung von Blockaden bei Hardware, Zugriff oder Netzwerk |
| Abgabebestätigung | admin.wb@tbz.zh.ch | Nach Abgabe, spätestens 18.12.2026 | E-Mail | Bestätigung gemäss Merkblatt A |
| Dokumentationsstand | Beide Experten | Laufend, kein Push ohne aktualisierte Dokumentation | GitHub Pages | Jederzeitiger Zugriff auf den aktuellen Entwicklungsstand |

Repository, Dokumentation und Project Board sind öffentlich. Die drei Links werden beim Kickoff versendet. Die öffentliche Erreichbarkeit des Boards wird in Sprint 1 aus einem abgemeldeten Browser verifiziert und im Statusbericht der Kalenderwoche 38 bestätigt.

### 2.5 Projektstrukturplan

Das Projekt ist in elf Arbeitspakete zerlegt, die im Folgenden als Epics bezeichnet werden. Jedes Epic bündelt fachlich zusammengehörende User Stories. Die Epics sind sechs übergeordneten Bereichen von der Projektführung bis zum Abschluss zugeordnet.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 746 592" width="746" height="592" role="img" aria-label="Projektstrukturplan mit elf Epics" class="dia-svg"><style>.dia-svg text{font-family:IBM Plex Sans,system-ui,sans-serif;fill:var(--md-default-fg-color,#1a1a1a)}.dia-svg .k{font-size:14px}.dia-svg .kb{font-size:14px;font-weight:600}.dia-svg rect{fill:var(--md-default-bg-color,#fff);stroke:var(--md-default-fg-color--lighter,#bbb)}.dia-svg rect.w{fill:var(--md-code-bg-color,#f2f2f2)}.dia-svg path{fill:none;stroke:var(--md-default-fg-color--lighter,#bbb);stroke-width:1.2}</style><rect class="" x="400" y="16" width="330" height="40" rx="5"/><text class="k" x="412" y="41.0">E1  Projektinitialisierung</text><rect class="w" x="200" y="16.0" width="150" height="40" rx="5"/><text class="kb" x="212" y="41.0">Projektführung</text><path d="M 350 36.0 H 375.0 V 36.0 H 400"/><rect class="" x="400" y="68" width="330" height="40" rx="5"/><text class="k" x="412" y="93.0">E2  IST-Aufnahme und Ausgangsmessung</text><rect class="w" x="200" y="68.0" width="150" height="40" rx="5"/><text class="kb" x="212" y="93.0">Analyse</text><path d="M 350 88.0 H 375.0 V 88.0 H 400"/><rect class="" x="400" y="120" width="330" height="40" rx="5"/><text class="k" x="412" y="145.0">E3  On-Prem-Plattform</text><rect class="" x="400" y="172" width="330" height="40" rx="5"/><text class="k" x="412" y="197.0">E4  Public Cloud</text><rect class="w" x="200" y="146.0" width="150" height="40" rx="5"/><text class="kb" x="212" y="171.0">Plattform</text><path d="M 350 166.0 H 375.0 V 140.0 H 400"/><path d="M 350 166.0 H 375.0 V 192.0 H 400"/><rect class="" x="400" y="224" width="330" height="40" rx="5"/><text class="k" x="412" y="249.0">E5  Fachmodell</text><rect class="" x="400" y="276" width="330" height="40" rx="5"/><text class="k" x="412" y="301.0">E6  Agent</text><rect class="" x="400" y="328" width="330" height="40" rx="5"/><text class="k" x="412" y="353.0">E7  MCP-Adapter</text><rect class="w" x="200" y="276.0" width="150" height="40" rx="5"/><text class="kb" x="212" y="301.0">Lösung</text><path d="M 350 296.0 H 375.0 V 244.0 H 400"/><path d="M 350 296.0 H 375.0 V 296.0 H 400"/><path d="M 350 296.0 H 375.0 V 348.0 H 400"/><rect class="" x="400" y="380" width="330" height="40" rx="5"/><text class="k" x="412" y="405.0">E8  Validierung und Messung</text><rect class="" x="400" y="432" width="330" height="40" rx="5"/><text class="k" x="412" y="457.0">E9  Bewertung und Vergleich</text><rect class="w" x="200" y="406.0" width="150" height="40" rx="5"/><text class="kb" x="212" y="431.0">Nachweis</text><path d="M 350 426.0 H 375.0 V 400.0 H 400"/><path d="M 350 426.0 H 375.0 V 452.0 H 400"/><rect class="" x="400" y="484" width="330" height="40" rx="5"/><text class="k" x="412" y="509.0">E10  Betrieb und Schulung</text><rect class="" x="400" y="536" width="330" height="40" rx="5"/><text class="k" x="412" y="561.0">E11  Architektur und Abschluss</text><rect class="w" x="200" y="510.0" width="150" height="40" rx="5"/><text class="kb" x="212" y="535.0">Abschluss</text><path d="M 350 530.0 H 375.0 V 504.0 H 400"/><path d="M 350 530.0 H 375.0 V 556.0 H 400"/><rect class="w" x="8" y="237.0" width="150" height="40" rx="5"/><text class="kb" x="20" y="262.0">Diplomarbeit</text><path d="M 158 257.0 H 179.0 V 36.0 H 200"/><path d="M 158 257.0 H 179.0 V 88.0 H 200"/><path d="M 158 257.0 H 179.0 V 166.0 H 200"/><path d="M 158 257.0 H 179.0 V 296.0 H 200"/><path d="M 158 257.0 H 179.0 V 426.0 H 200"/><path d="M 158 257.0 H 179.0 V 530.0 H 200"/></svg>

Die Gliederung folgt dem fachlichen Ablauf des Projekts, von der Analyse über den Aufbau der Plattformen und die Entwicklung der Lösung bis zum Nachweis und zum Abschluss. Die Zuordnung der Epics zu Sprints, Stories und Story Points steht in Kapitel 2.8.

### 2.6 Termin- und Meilensteinplan

Das Projekt läuft über 14 Kalenderwochen, von KW38 bis KW51 2026. Die Sprintgrenzen sind an die drei fixen Zwischenpräsentationstermine aus Merkblatt A gekoppelt.

| Sprint | Zeitraum | Kalenderwochen | Dauer | Sprintziel in einem Satz |
| --- | --- | --- | --- | --- |
| Sprint 1 | 14.09.2026 bis 18.10.2026 | KW38 bis KW42 | 5 Wochen | Die Ausgangslage ist gemessen, beide Zielplattformen sind nutzbar, die Architektur ist entschieden |
| Sprint 2 | 19.10.2026 bis 15.11.2026 | KW43 bis KW46 | 4 Wochen | Fachmodell, Agent und der erste vollständige End-to-End-Durchlauf lokal stehen |
| Sprint 3 | 16.11.2026 bis 18.12.2026 | KW47 bis KW51 | 5 Wochen | Beide Plattformen sind validiert, Vergleich und Bewertung sind abgeschlossen, die Abgabe ist erfolgt |

Jeder Sprint endet mit einer Zwischenpräsentation, die zugleich als Sprint Review dient. Die unterschiedliche Länge der Sprints ergibt sich aus den fixen Terminen und ist in Kapitel 2.6.1 begründet.

**Meilensteine**

Sechs Meilensteine strukturieren den Projektverlauf. Jeder Meilenstein ist mit einem Freigabekriterium hinterlegt, anhand dessen entschieden wird, ob er erreicht ist.

| ID | Meilenstein | Termin | Freigabekriterium | Beteiligte |
| --- | --- | --- | --- | --- |
| M0 | Projektstart und Kickoff | 14.09.2026 | Zugänge geklärt, Hardware freigegeben, Board und Repository für die Experten erreichbar, Abgrenzung bestätigt | Diplomand, beide Experten |
| M1 | Zwischenpräsentation 1, Sprint 1 Review | Woche vom 19.10.2026 | Ausgangsmessung vorliegend, lokale Plattform nutzbar, Cloud-Smoke-Test bestanden, Architektur entschieden | Diplomand, beide Experten |
| M2 | Zwischenpräsentation 2, Sprint 2 Review | Woche vom 16.11.2026 | Modell, Schema und Agent funktionsfähig, ein vollständiger Durchlauf lokal demonstriert | Diplomand, beide Experten |
| M3 | Scope-Freeze | 04.12.2026 | Keine neuen Funktionen mehr, ab hier nur noch Tests, Messungen, Dokumentation und Korrekturen | Diplomand |
| M4 | Zwischenpräsentation 3, Sprint 3 Review | Woche vom 14.12.2026 | Sechs Durchläufe protokolliert, Vergleich und Bewertung vorliegend, Dokumentation abgabefertig | Diplomand, beide Experten |
| M5 | Abgabe der Diplomarbeit | 18.12.2026 | Dokumentation über GitHub Pages bereitgestellt, Management Summary mit unterschriebenem Ehrenwort abgelegt, Experten informiert, Bestätigungsmail versendet | Diplomand |
| M6 | Kolloquium | Woche vom 04.01.2027 | Raum reserviert, Präsentation und Demo inklusive Backup-Plan bereit | Diplomand, beide Experten |

Der Scope-Freeze M3 liegt bewusst zwei Wochen vor der Abgabe, damit die verbleibende Zeit für Tests, Messungen und die Fertigstellung der Dokumentation zur Verfügung steht. Das folgende Balkendiagramm zeigt die zeitliche Lage der Epics und der Meilensteine.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 902 728" width="902" height="728" role="img" aria-label="Terminplan der Diplomarbeit" class="dia-svg"><style>.dia-svg text{font-family:IBM Plex Sans,system-ui,sans-serif;fill:var(--md-default-fg-color,#1a1a1a)}.dia-svg .k{font-size:13px}.dia-svg .kb{font-size:13px;font-weight:600}.dia-svg .ax{font-size:11px;fill:var(--md-default-fg-color--light,#666)}.dia-svg .bar{fill:var(--md-primary-fg-color,#4051b5);opacity:.85}.dia-svg .ms{fill:var(--md-accent-fg-color,#526cfe)}.dia-svg .grid{stroke:var(--md-default-fg-color--lightest,#e3e3e3);stroke-width:1}.dia-svg .band{fill:var(--md-code-bg-color,#f5f5f5)}</style><rect class="band" x="16" y="42" width="870" height="222" rx="4"/><text class="kb" x="24" y="62">Sprint 1, 14.09. bis 18.10.2026</text><text class="k" x="32" y="93.0">E1  Projektinitialisierung</text><rect class="bar" x="266.0" y="79" width="44.7" height="20" rx="4"/><text class="k" x="32" y="125.0">E2  IST-Aufnahme</text><rect class="bar" x="278.8" y="111" width="159.8" height="20" rx="4"/><text class="k" x="32" y="157.0">E3  On-Prem-Plattform</text><rect class="bar" x="266.0" y="143" width="89.5" height="20" rx="4"/><text class="k" x="32" y="189.0">E4  Public Cloud</text><rect class="bar" x="400.2" y="175" width="63.9" height="20" rx="4"/><text class="k" x="32" y="221.0">E11 Zielarchitektur</text><rect class="bar" x="400.2" y="207" width="89.5" height="20" rx="4"/><text class="k" x="32" y="253.0">Zwischenpräsentation 1</text><path class="ms" d="M 489.7 240 l 8 9.0 l -8 9.0 l -8 -9.0 Z"/><text class="kb" x="24" y="284">Sprint 2, 19.10. bis 15.11.2026</text><text class="k" x="32" y="315.0">E5  Fachmodell</text><rect class="bar" x="489.7" y="301" width="63.9" height="20" rx="4"/><text class="k" x="32" y="347.0">E6  Agent</text><rect class="bar" x="534.5" y="333" width="89.5" height="20" rx="4"/><text class="k" x="32" y="379.0">E7  Adapter KubeVirt</text><rect class="bar" x="579.2" y="365" width="83.1" height="20" rx="4"/><text class="k" x="32" y="411.0">Zwischenpräsentation 2</text><path class="ms" d="M 668.7 398 l 8 9.0 l -8 9.0 l -8 -9.0 Z"/><rect class="band" x="16" y="422" width="870" height="286" rx="4"/><text class="kb" x="24" y="442">Sprint 3, 16.11. bis 18.12.2026</text><text class="k" x="32" y="473.0">E7  Adapter Public Cloud</text><rect class="bar" x="668.7" y="459" width="89.5" height="20" rx="4"/><text class="k" x="32" y="505.0">E8  Validierung und Messung</text><rect class="bar" x="713.4" y="491" width="89.5" height="20" rx="4"/><text class="k" x="32" y="537.0">E9  Bewertung und Vergleich</text><rect class="bar" x="758.2" y="523" width="76.7" height="20" rx="4"/><text class="k" x="32" y="569.0">E10 Betrieb und Schulung</text><rect class="bar" x="764.6" y="555" width="63.9" height="20" rx="4"/><text class="k" x="32" y="601.0">E11 Dokumentation und Abschluss</text><rect class="bar" x="783.7" y="587" width="89.5" height="20" rx="4"/><text class="k" x="32" y="633.0">Scope-Freeze</text><path class="ms" d="M 783.7 620 l 8 9.0 l -8 9.0 l -8 -9.0 Z"/><text class="k" x="32" y="665.0">Zwischenpräsentation 3</text><path class="ms" d="M 847.6 652 l 8 9.0 l -8 9.0 l -8 -9.0 Z"/><text class="k" x="32" y="697.0">Abgabe</text><path class="ms" d="M 873.2 684 l 8 9.0 l -8 9.0 l -8 -9.0 Z"/><line class="grid" x1="374.7" y1="40" x2="374.7" y2="712"/><text class="ax" x="374.7" y="34" text-anchor="middle">01.10.</text><line class="grid" x1="572.8" y1="40" x2="572.8" y2="712"/><text class="ax" x="572.8" y="34" text-anchor="middle">01.11.</text><line class="grid" x1="764.6" y1="40" x2="764.6" y2="712"/><text class="ax" x="764.6" y="34" text-anchor="middle">01.12.</text><text class="ax" x="266.0" y="34">14.09.</text><text class="ax" x="873.2" y="34" text-anchor="end">18.12.</text></svg>

#### 2.6.1 Begründung der unterschiedlichen Sprintlängen

Die drei Sprints sind mit fünf, vier und fünf Wochen unterschiedlich lang. Diese Abweichung von der üblichen Gleichmässigkeit ist beabsichtigt und wird nachfolgend begründet.

Die drei Zwischenpräsentationen sind in Merkblatt A auf die Wochen vom 19.10., 16.11. und 14.12.2026 festgelegt und in der bewilligten Projektbeschreibung als Sprint Reviews vereinbart. Da ein Sprint Review an das Sprintende gehört, geben diese Termine die Sprintgrenzen vor. Die Abstände zwischen ihnen betragen vier bis fünf Wochen und sind nicht gleich lang. Daraus ergeben sich zwei Möglichkeiten:

1. Gleich lange Sprints von zwei Wochen. Dann fallen die Reviews mitten in einen Sprint und die wichtigsten Steuerungstermine des Projekts sind von den Sprintgrenzen entkoppelt.
2. Sprints entlang der fixen Termine. Dann sind die Sprints unterschiedlich lang, dafür ist jeder Review ein echter Sprintabschluss mit einem demonstrierbaren Increment.

Gewählt wurde Variante 2, weil ein Review mit Steuerungswirkung für das Projekt mehr Nutzen bringt als die formale Gleichmässigkeit der Sprintlänge. Die Vergleichbarkeit der Sprints wird auf anderem Weg sichergestellt. Die Planung erfolgt nicht pauschal pro Sprint, sondern über ein konstantes Story-Point-Budget pro Woche, wie in Kapitel 2.9 beschrieben. Ein fünfwöchiger Sprint erhält damit fünf Wochenbudgets und ein vierwöchiger vier, wodurch die Velocity über die Sprints hinweg vergleichbar bleibt.

Zusätzlich wird in den längeren Sprints nach der Hälfte der Laufzeit ein Zwischenabgleich durchgeführt und im jeweiligen Statusbericht dokumentiert. Damit bleibt die Kontrolldichte auch in einem Fünfwochensprint erhalten.

### 2.7 Sprintstruktur und Events

Jeder Sprint folgt demselben Ablauf aus Planung, Durchführung, Review und Retrospektive.

**Sprint Planning, am ersten Tag des Sprints**

- Sprintziel als ein Satz Outcome formulieren
- Story-Point-Budget aus der Wochenkapazität berechnen
- User Stories aus dem priorisierten Backlog ziehen, bis das Budget erreicht ist
- Definition of Ready für jede gezogene Story prüfen
- Sprint-Feld und Milestone im Project Board setzen
- Sprintplanung im Repository ablegen

**Sprint Execution, laufend**

- Work in Progress Limit: maximal zwei Issues gleichzeitig in der Spalte In Progress
- Journaleintrag pro Arbeitseinheit
- Nachweise entstehen mit der Umsetzung, nicht nachträglich
- Wöchentlicher Statusbericht jeden Freitag
- Arbeitsweise und Branching siehe Kapitel 2.12

**Sprint Review, am Sprintende, zugleich Zwischenpräsentation**

Ablauf, 45 bis 60 Minuten:

1. Sprintziel und was daraus wurde, 5 Minuten
2. Abgleich gegen die Zieltabelle aus Kapitel 1.4, 5 Minuten
3. Demo des lauffähigen Standes, 15 Minuten
4. Herausforderungen, Entscheide und Abweichungen, 10 Minuten
5. Risikolage und Ausblick auf den nächsten Sprint, 5 Minuten
6. Fragen und Rückmeldung der Experten, 15 Minuten

Die Rückmeldungen der Experten werden im Reviewdokument protokolliert und als Issues in den Backlog aufgenommen. Damit ist nachvollziehbar, wie jede Rückmeldung weiterverarbeitet wurde und in welchem Sprint sie umgesetzt worden ist.

**Sprint Retrospektive, direkt nach dem Review**

Die Reflexion erfolgt mit dem Starfish-Modell entlang der fünf Kategorien Keep, Stop, Start, More of und Less of. Aus der Retrospektive werden höchstens drei konkrete Massnahmen für den Folgesprint abgeleitet, damit die Umsetzung realistisch bleibt. Die Umsetzung dieser Massnahmen wird in der nächsten Retrospektive überprüft.

### 2.8 Anforderungsmanagement und Product Backlog

Jede Anforderung wird als GitHub Issue nach dem Schema `Als <Rolle> möchte ich <Ziel>, damit <Nutzen>` erfasst und im öffentlichen Project Board gesteuert. Der Backlog umfasst **38 User Stories** mit insgesamt **113 Story Points**, verteilt auf elf Epics und drei Sprints.

#### Verteilung über die Sprints

| Sprint | Zeitraum | Dauer | Stories | Story Points | Sprintziel |
| --- | --- | --- | --- | --- | --- |
| Sprint 1 | 14.09.2026 bis 18.10.2026 | 5 Wochen | 17 | 40 | Die Ausgangslage ist gemessen, beide Zielplattformen sind nutzbar und die Architektur ist entschieden. |
| Sprint 2 | 19.10.2026 bis 15.11.2026 | 4 Wochen | 8 | 32 | Fachmodell, Agent und der erste vollständige End-to-End-Durchlauf auf der lokalen Plattform stehen. |
| Sprint 3 | 16.11.2026 bis 18.12.2026 | 5 Wochen | 13 | 41 | Beide Zielplattformen sind validiert, Vergleich und Bewertung sind abgeschlossen, die Arbeit ist abgegeben. |
| Total | 14.09. bis 18.12.2026 | 14 Wochen | 38 | 113 | |

#### Verteilung über die Epics

| Epic | Thema | Stories | Story Points | Sprint |
| --- | --- | --- | --- | --- |
| E1 | Projektinitialisierung | 6 | 10 | 1 |
| E2 | IST-Aufnahme und Ausgangsmessung | 4 | 13 | 1 |
| E3 | On-Prem Plattform | 4 | 9 | 1 |
| E4 | Public Cloud | 2 | 5 | 1 |
| E5 | Fachmodell | 2 | 8 | 2 |
| E6 | Agent | 4 | 16 | 2 |
| E7 | MCP-Adapter | 3 | 16 | 2, 3 |
| E8 | Validierung und Messung | 4 | 10 | 3 |
| E9 | Bewertung und Vergleich | 4 | 12 | 3 |
| E10 | Betrieb und Schulung | 2 | 5 | 3 |
| E11 | Architektur und Projektabschluss | 3 | 9 | 1, 3 |

#### Standards pro Issue

- User Story im genannten Schema
- Epic, Story Points und Priorität nach MoSCoW
- Definition of Ready als Checkbox-Liste
- Prüfbare Akzeptanzkriterien als Checkbox-Liste
- Definition of Done als Checkbox-Liste

Die vollständigen Akzeptanzkriterien jeder Story stehen im zugehörigen Issue und werden dort abgehakt. Dieses Kapitel führt den Backlog als Übersicht, damit der Stand im Board und der Stand in der Dokumentation nicht auseinanderlaufen.

Nachweise werden grundsätzlich in der Dokumentation platziert, an der Stelle, die sie belegen. Wo ein besonderer Nachweis nötig ist, etwa ein Mess-, Lauf- oder Kostenprotokoll, ist er im jeweiligen Akzeptanzkriterium ausdrücklich verlangt.

---

#### Sprint 1: 14.09.2026 bis 18.10.2026

**Sprintziel:** Die Ausgangslage ist gemessen, beide Zielplattformen sind nutzbar und die Architektur ist entschieden.

**Umfang:** 17 User Stories, 40 Story Points, 5 Wochen

Die Stories liegen im Milestone Sprint 1 des Project Boards.

| ID | Titel | Epic | SP | Prio |
| --- | --- | --- | --- | --- |
| US01 | Repository mit klarer Struktur | E1 | 2 | Must |
| US02 | Öffentlich einsehbares Project Board | E1 | 2 | Must |
| US03 | Vorlagen, Labels, Milestones und Regeln | E1 | 1 | Must |
| US04 | Dokumentation über GitHub Pages | E1 | 2 | Must |
| US05 | Journal und Statusbericht als feste Routine | E1 | 1 | Must |
| US06 | Kickoff mit den Experten | E1 | 2 | Must |
| US07 | IST-Analyse der heutigen Bereitstellung | E2 | 2 | Must |
| US08 | Test-Lernumgebung aus m239, m254 und m426 ableiten | E2 | 3 | Must |
| US09 | Messkonzept mit identischen Start- und Endkriterien | E2 | 3 | Must |
| US10 | Ausgangsmessung am heutigen Vorgehen | E2 | 5 | Must |
| US11 | Hardware betriebsbereit und dokumentiert | E3 | 2 | Must |
| US12 | Kubernetes-Cluster verifizieren und dokumentieren | E3 | 2 | Must |
| US13 | KubeVirt verifizieren und Storage klären | E3 | 2 | Must |
| US38 | Referenz-VM manuell erstellen und wieder abbauen | E3 | 3 | Must |
| US14 | Auswahl der Public Cloud als Nutzwertanalyse | E4 | 2 | Must |
| US15 | Cloud-Smoke-Test mit Budgetwarnung und Quotas | E4 | 3 | Must |
| US16 | Zielarchitektur, ADRs und Zwischenpräsentation 1 | E11 | 3 | Must |

#### Sprint 2: 19.10.2026 bis 15.11.2026

**Sprintziel:** Fachmodell, Agent und der erste vollständige End-to-End-Durchlauf auf der lokalen Plattform stehen.

**Umfang:** 8 User Stories, 32 Story Points, 4 Wochen

Die Stories liegen im Milestone Sprint 2 des Project Boards.

| ID | Titel | Epic | SP | Prio |
| --- | --- | --- | --- | --- |
| US17 | Plattformneutrales YAML-Modell für Lernumgebungen | E5 | 5 | Must |
| US18 | JSON-Schema mit positiver und negativer Validierung | E5 | 3 | Must |
| US19 | Agent-Grundgerüst mit Kommandozeilenschnittstelle | E6 | 3 | Must |
| US20 | Persistenter Zustandsspeicher mit Zustandsübergängen | E6 | 5 | Must |
| US21 | create und status | E6 | 5 | Must |
| US22 | reset und delete | E6 | 3 | Must |
| US23 | Einheitliches Funktionsset über MCP | E7 | 3 | Must |
| US24 | MCP-Adapter für KubeVirt, erster End-to-End-Durchlauf | E7 | 5 | Must |

#### Sprint 3: 16.11.2026 bis 18.12.2026

**Sprintziel:** Beide Zielplattformen sind validiert, Vergleich und Bewertung sind abgeschlossen, die Arbeit ist abgegeben.

**Umfang:** 13 User Stories, 41 Story Points, 5 Wochen

Die Stories liegen im Milestone Sprint 3 des Project Boards.

| ID | Titel | Epic | SP | Prio |
| --- | --- | --- | --- | --- |
| US25 | MCP-Adapter für die Public Cloud | E7 | 8 | Must |
| US26 | Automatisierter Readiness-Check | E8 | 2 | Must |
| US27 | Drei vollständige Durchläufe auf der lokalen Plattform | E8 | 2 | Must |
| US28 | Drei vollständige Durchläufe in der Public Cloud | E8 | 3 | Must |
| US29 | Nachweis des vollständigen Abbaus | E8 | 3 | Must |
| US30 | Vorher-Nachher-Vergleich | E9 | 3 | Must |
| US31 | Bewertung der MCP-Architektur gegen eine direkte API-Anbindung | E9 | 3 | Must |
| US32 | Wirtschaftlichkeitsbetrachtung | E9 | 3 | Must |
| US33 | Beurteilung der Übertragbarkeit in den Produktivbetrieb | E9 | 3 | Must |
| US34 | Runbook für Aufbau, Bedienung, Fehleranalyse und Abbau | E10 | 2 | Must |
| US35 | Schulungsunterlage und Einführung | E10 | 3 | Must |
| US36 | Dokumentation finalisieren, Management Summary, Ehrenwort | E11 | 3 | Must |
| US37 | Kolloquiumspräsentation und Demo-Skript | E11 | 3 | Must |

#### Nicht eingeplant, bewusst ausserhalb des Umfangs

| Thema | Einstufung |
| --- | --- |
| Migration oder Abschaltung der bestehenden MAAS-Umgebung | Won't |
| Vollständige Umsetzung aller Unterrichtsmodule | Won't |
| Sprachmodellbasierte Entscheidungslogik | Won't |
| Bedienoberfläche | Won't |
| Zweite Public Cloud | Won't |
| GitOps oder Argo CD | Won't |
| Mehrknoten-Cluster und Hochverfügbarkeit | Won't |
| Verteilter Storage und produktive Skalierung | Won't |
| Hardwarebeschaffung und betriebliche Netzwerkumstellungen | Won't |

Diese Punkte sind im bewilligten Antrag abgegrenzt und werden im Ausblick in Kapitel 10 behandelt.

#### Umgang mit Puffern und Umfangsreduktion

Das Budget orientiert sich an der geplanten Kapazität von acht Story Points pro Woche. Sprint 3 liegt mit 41 Punkten einen Punkt über diesem Budget. Die Abweichung entstand, als die Klärung der künftigen Zuständigkeiten nachträglich in US33 aufgenommen wurde. Sie wird bewusst in Kauf genommen und im Statusbericht mitgeführt, statt die Story kleiner zu schätzen, als sie ist.

Ein Zeitpuffer entsteht nicht durch freie Wochen, sondern durch die Steuerungsregel aus Kapitel 2.1.1: Bei Verzug wird der Umfang reduziert, nicht der Termin verschoben.

Die Reihenfolge der Reduktion ist vorab festgelegt und mit dem Firmenexperten abgestimmt:

1. US35 wird auf eine schriftliche Schulungsunterlage ohne durchgeführte Einführung reduziert
2. US33 wird auf eine qualitative Kurzbeurteilung reduziert
3. US34 wird auf die Kernabläufe Aufbau und Abbau beschränkt

Die übrigen Must-Stories des verbindlichen Kernumfangs bleiben in jedem Fall bestehen.

### 2.9 Aufwandschätzung, Kapazität und Velocity

**Warum Story Points und nicht Stunden**

Geschätzt wird relativ in Story Points. Eine Schätzung in Stunden würde bei Aufgaben mit hohem Lern- und Analyseanteil, etwa der erstmaligen Anbindung einer Public-Cloud-API, eine Scheingenauigkeit erzeugen. Story Points bewerten stattdessen Aufwand, Komplexität, Unsicherheit und Risiko gemeinsam.

**Schätzskala und Referenzstory**

Geschätzt wird auf einer angepassten Fibonacci-Skala. Als Referenz dient US01, die Einrichtung des Repositories mit Grundstruktur, bewertet mit 2 Story Points. Alle weiteren Stories werden im Verhältnis dazu eingeordnet.

| Story Points | Bedeutung | Beispiel aus diesem Projekt |
| --- | --- | --- |
| 1 | Sehr klein, klar abgegrenzt, kein Risiko | US03 Labels, Milestones und Regeln anlegen |
| 2 | Klein, bekannte Technik, überschaubarer Aufwand | US01 Repository mit Grundstruktur, Referenzstory |
| 3 | Mittel, mehrere Schritte oder eine Abhängigkeit | US09 Messkonzept definieren |
| 5 | Komplex, neue Technologie, erhöhter Analyse- und Debuggingaufwand | US20 Zustandsspeicher mit Zustandsübergängen |
| 8 | Sehr komplex, viele Unbekannte, hohes Risiko | US25 MCP-Adapter für die Public Cloud |
| 13 | Zu gross, muss zerlegt werden | Wird nicht in einen Sprint gezogen |

Eine Story mit 13 Punkten gilt als nicht planbar und wird vor der Sprintaufnahme zerlegt. Eine Story mit 8 Punkten wird geprüft, ob sich ein kleinerer, eigenständig nutzbarer Teil abtrennen lässt. US25 ist die einzige Story mit 8 Punkten und wurde bewusst nicht zerlegt, weil der Nachweis der Plattformunabhängigkeit nur als Ganzes aussagekräftig ist.

**Kapazität**

Die Kapazitätsplanung geht von der Zeit aus, die neben Beruf und Unterricht zur Verfügung steht, und rechnet diese in ein Story-Point-Budget pro Sprint um.

| Grösse | Wert | Herleitung |
| --- | --- | --- |
| Verfügbare Zeit pro Woche | ca. 14 Stunden | Zeit anstelle des Unterrichts plus Selbststudium |
| Arbeitsrhythmus | Abende unter der Woche, Mittwoch als freier Tag, Wochenende | Der Diplomand arbeitet 80 Prozent, der Mittwoch dient als Labortag für Arbeiten an der Hardware |
| Geplante Velocity pro Woche | 8 Story Points | Erstschätzung aus der Referenzstory, ab Sprint 2 durch Ist-Werte ersetzt |
| Sprint 1, 5 Wochen | 40 Story Points | 5 mal 8 |
| Sprint 2, 4 Wochen | 32 Story Points | 4 mal 8 |
| Sprint 3, 5 Wochen | 40 Story Points | 5 mal 8 |
| Gesamtbudget | 112 Story Points | Entspricht dem Umfang des Product Backlogs |

Für die Diplomarbeit steht während der Arbeitszeit bei der TBZ keine Zeit zur Verfügung. Die Arbeit erfolgt ausserhalb der Arbeitszeit und an den Schultagen des Lehrgangs.

**Velocity-Verfolgung**

| Sprint | Geplant | Abgeschlossen | Velocity pro Woche | Abweichung | Konsequenz für die Folgeplanung |
| --- | --- | --- | --- | --- | --- |
| Sprint 1 | 40 | | | | |
| Sprint 2 | 32 | | | | |
| Sprint 3 | 40 | | | | |

Die Tabelle wird an jedem Sprintende ausgefüllt. Weicht die tatsächliche Velocity um mehr als 20 Prozent von der geplanten ab, wird das Budget des Folgesprints angepasst und die Anpassung im Statusbericht begründet.

Die Summenbildung erfolgt über das Feld Story Points im Project Board, das als Zahlenfeld angelegt ist und die Gruppierung nach Sprint mit Summe erlaubt.

### 2.10 Priorisierung

Priorisiert wird nach MoSCoW. Die Priorität wird pro Issue im Board gesetzt und bleibt über die Sprints hinweg sichtbar.

| Priorität | Bedeutung |
| --- | --- |
| Must | Gehört zum verbindlichen Kernumfang der Projektbeschreibung. Ohne diese Story gilt der Proof of Concept als nicht erfolgreich |
| Should | Wichtig für Qualität und Nachvollziehbarkeit, der Kernumfang bleibt ohne sie aber nachweisbar |
| Could | Verbesserung, wird nur bei freier Kapazität umgesetzt |
| Won't | Bewusst ausserhalb des Umfangs, wird im Ausblick behandelt |

Alle 38 User Stories des Backlogs sind als Must eingestuft. Das ist eine Konsequenz aus der Abgrenzung: Der Umfang wurde bereits im Antrag so eng gefasst, dass jede verbleibende Story ein Erfolgskriterium belegt. Die Flexibilität liegt deshalb nicht in der Priorisierung, sondern in der in Kapitel 2.8 festgelegten Reihenfolge der Umfangsreduktion.

Ergänzend zur MoSCoW-Einstufung entscheiden bei gleicher Priorität folgende Kriterien über die Reihenfolge:

1. Technische Abhängigkeit, blockierende Stories zuerst
2. Risikoreduktion, Stories die ein hoch bewertetes Risiko entschärfen zuerst
3. Nachweisrelevanz, Stories die ein Erfolgskriterium der Projektbeschreibung belegen
4. Rückmeldungen der Experten aus dem letzten Review

### 2.11 Definition of Ready und Definition of Done

**Definition of Ready, Eingangsschranke vor der Umsetzung**

Eine User Story darf erst in einen Sprint gezogen werden, wenn:

- Nutzen und Ziel formuliert sind
- die Akzeptanzkriterien prüfbar sind, also eine Aussage über bestanden oder nicht bestanden zulassen
- Abhängigkeiten und Vorbedingungen benannt sind
- Story Points geschätzt, Epic und Priorität gesetzt sind
- klar ist, welcher Nachweis am Ende vorliegen muss

**Definition of Done pro User Story**

- Akzeptanzkriterien erfüllt
- Änderungen sind auf main
- Der zugehörige Dokumentationsabschnitt ist geschrieben oder aktualisiert
- Der Nachweis ist in der Dokumentation platziert, an der Stelle, die er belegt
- Wiederholbarkeit: Der Schritt lässt sich allein anhand der Dokumentation ein zweites Mal ausführen
- Keine Zugangsdaten oder Geheimnisse im Repository
- Das Issue ist im Board auf Done

**Projektweite Definition of Done**

Die projektweite Definition of Done entspricht den sieben Erfolgskriterien des Proof of Concept in Kapitel 1.5. Sie werden an jedem Sprintende überprüft und der Erfüllungsgrad im Statusbericht ausgewiesen.

### 2.12 Arbeitsweise, Branching und Teststrategie

#### Versionsverwaltung

Das Projekt nutzt einen einzigen dauerhaften Branch, `main`. Force Pushes sind blockiert. Auf ein verpflichtendes Pull-Request-Verfahren wird bewusst verzichtet.

| Art der Änderung | Vorgehen | Begründung |
| --- | --- | --- |
| Dokumentation, Statusberichte, Journal, Nachweise | Direkt auf `main` | Rund zwei Drittel des Aufwands entfallen auf Dokumentation und Analyse. Ein Pull Request pro Journaleintrag erzeugt zusätzlichen Aufwand ohne Erkenntnisgewinn |
| Infrastrukturkonfiguration, die auf den Zielsystemen erarbeitet wurde | Direkt auf `main` | Das Ergebnis steht bereits auf der Maschine, der Commit dokumentiert es |
| Agent, Adapter, Fachmodell, Schema | Kurzlebiger Feature Branch, Merge nach `main` erst wenn die Tests grün sind | Hier kann ein unfertiger Stand den lauffähigen Zustand auf `main` beeinträchtigen |

Branchnamen folgen dem Schema `<typ>/<US-Nummer>-<kurz>`, zum Beispiel `feat/US21-create-status`. Die Story-Nummer verbindet Branch, Issue und Commit zu einer durchgehenden Nachweiskette. Lebt ein Branch länger als drei Arbeitstage, gilt die Story als zu gross geschnitten.

Commit Messages folgen den Conventional Commits und sind auf Englisch verfasst, die Dokumentation auf Deutsch. Ein Commit, der eine Story abschliesst, enthält `Closes #<Nummer>`. Damit bleibt die Verbindung zwischen Issue, Änderung und Dokumentationsabschnitt auch ohne Pull Request vollständig.

Nach jeder Zwischenpräsentation wird der präsentierte Stand mit einem Git-Tag markiert, `zp1`, `zp2`, `zp3`, dazu `scope-freeze` und `abgabe`. Damit ist jeder gezeigte Stand später reproduzierbar.

#### Warum kein GitOps

Die bewilligte Projektbeschreibung schliesst GitOps und Argo CD ausdrücklich aus. Neben dieser formalen Vorgabe gibt es auch eine fachliche Begründung, die nachfolgend dargelegt wird.

GitOps ist ein pull-basierter Reconciliation-Loop: Ein Controller im Cluster vergleicht laufend den Ist-Zustand mit dem in Git beschriebenen Soll-Zustand und gleicht Abweichungen selbsttätig aus. Der Agent dieser Arbeit arbeitet dagegen imperativ und befehlsgesteuert. Die Operationen create, status, reset und delete laufen dann, wenn sie aufgerufen werden, und der Zustand liegt im Zustandsspeicher des Agenten.

Dieses Verhalten ergibt sich aus der Anforderung und stellt keine Einschränkung dar. Eine Lernumgebung soll für eine Lektion entstehen und danach vollständig verschwinden, während ein Reconciliation-Loop sie nach jedem delete erneut aufbauen würde. Git ist in dieser Arbeit damit die Quelle der Definition und nicht die Quelle des Laufzeitzustands.

#### Teststrategie

Das Repository ist bewusst nicht mit den Zielsystemen verbunden. Der CI-Runner läuft bei einem externen Anbieter und hat keinen Zugang zum Labornetz der TBZ. Daraus ergibt sich eine zweiteilige Teststrategie.

**Ebene 1, automatisiert in der Pipeline bei jedem Push auf einen Feature Branch**

| Test | Was geprüft wird | Infrastruktur nötig |
| --- | --- | --- |
| Lint | Codeformat und offensichtliche Fehler | nein |
| Schemavalidierung | Eine gültige Definition wird akzeptiert, eine ungültige abgewiesen | nein |
| Zustandsmaschine | Erlaubte und unerlaubte Zustandsübergänge, Idempotenz | nein |
| Adapter-Contract-Tests | Der Agent ruft die richtigen Funktionen in der richtigen Reihenfolge auf, geprüft gegen einen Fake-Adapter | nein |
| Dokumentationsbau | Die Dokumentation baut im strikten Modus, keine toten Verweise | nein |

Der Fake-Adapter dient dabei nicht nur als Testhilfsmittel, sondern ist eine dritte Implementierung derselben MCP-Schnittstelle und belegt damit unmittelbar das Kriterium Testbarkeit in der Bewertung der Adapterarchitektur in Kapitel 6. Mit direkten API-Aufrufen im Agenten wäre eine Prüfung der Steuerungslogik ohne echte Infrastruktur nicht möglich.

**Ebene 2, manuell auf der Zielinfrastruktur**

Die sechs vollständigen Durchläufe werden auf dem lokalen Cluster und in der Public Cloud von Hand angestossen und protokolliert, wobei das Laufprotokoll und nicht ein grüner Pipeline-Status als Nachweis dient. Das entspricht den Erfolgskriterien der Projektbeschreibung, die ausdrücklich Durchläufe auf den Zielplattformen verlangen.

**Geprüft und verworfen**

Ein selbst gehosteter CI-Runner auf der Laborhardware würde der Pipeline Zugang zum Labornetz verschaffen. Bei einem öffentlichen Repository wird davon abgeraten, weil über einen Fork fremder Code auf der eigenen Maschine ausgeführt werden könnte, was in einem Schulnetz nicht vertretbar ist. Stattdessen werden die Integrationstests manuell durchgeführt und protokolliert.

### 2.13 Qualitätssicherung, Nachweisführung und Controlling

#### Nachweisstandard

Jede Aussage über einen erreichten Zustand ist durch einen Nachweis belegt. Der Nachweis steht grundsätzlich in der Dokumentation selbst, an der Stelle, die er belegt. Konsolenausgaben werden als Codeblock eingefügt, Screenshots als Abbildung eingebunden. Der Leser findet den Beleg damit dort, wo die Aussage steht, und muss ihn nicht in einem Anhang suchen.

Eine separate Ablage gibt es nur, wo sie fachlich nötig ist:

| Ausnahme | Warum separat | Ablage |
| --- | --- | --- |
| Bilddateien der Screenshots | Markdown bindet Bilder als Datei ein, der Screenshot selbst wird im Text angezeigt | `docs/img/` |
| Mess- und Laufprotokolle | Sechs Durchläufe mit Rohwerten, die in der Auswertung nur zusammengefasst erscheinen | `docs/messungen/`, ein File pro Lauf mit Lauf-Kennung |
| Umfangreiche Systemausgaben | Vollständige Auditausgaben, von denen im Text nur der relevante Ausschnitt steht | `docs/nachweise/` |

Alles andere, also Ergebnisse, Verifikationen, Fehlermeldungen und Zwischenstände, wird direkt in den zugehörigen Abschnitt geschrieben.

**Regel gegen Dokumentationsrückstand**

Ein Issue gilt nicht als erledigt, solange der zugehörige Dokumentationsabschnitt fehlt. Der Fortschritt der Dokumentation wird im wöchentlichen Statusbericht als eigene Ampel geführt.

#### Wöchentlicher Statusbericht

Jeden Freitag wird ein Statusbericht erstellt und unter `docs/status/` abgelegt, veröffentlicht über GitHub Pages. Zusätzlich wird im Teams-Kanal ein kurzer Post mit dem Link abgesetzt. Die Berichte sind nach Kalenderwoche nummeriert, von KW38 bis KW51, insgesamt vierzehn.

Fester Aufbau pro Bericht:

1. Ampel für Termin, Umfang, Qualität und Risiko
2. Sprintziel und Fortschritt in Story Points
3. Was diese Woche erreicht wurde, mit Issue-Nummern
4. Abweichungen vom Plan mit Ursache und Massnahme
5. Blockaden und was zu deren Auflösung nötig ist
6. Nächste Schritte in der Folgewoche
7. Änderungen in der Risikolage
8. Meilensteintrend

#### Ampeldefinition

Die Ampel des Statusberichts wird nach der Abweichung vom Plan gesetzt. Jeder Stufe ist eine feste Handlung zugeordnet, damit aus einer Bewertung auch eine Reaktion folgt.

| Farbe | Bedeutung | Handlung |
| --- | --- | --- |
| Grün | Im Plan, Abweichung unter 10 Prozent | Keine |
| Gelb | Abweichung zwischen 10 und 25 Prozent | Massnahme im Bericht benennen, im Folgesprint korrigieren |
| Rot | Abweichung über 25 Prozent oder Meilenstein gefährdet | Sofortige Information an den Firmenexperten, Umfangsreduktion prüfen |

Dieselbe Skala wird für alle vier Ampeln verwendet, also für Termin, Umfang, Qualität und Risiko.

#### Meilensteintrendanalyse

Für jeden Meilenstein wird wöchentlich der aktuell erwartete Termin erfasst. Eine waagrechte Linie über die Berichtswochen bedeutet, dass der Termin stabil ist. Eine steigende Linie zeigt eine drohende Verspätung früh an, lange bevor der Termin tatsächlich verstreicht.

| Meilenstein | Plantermin | KW38 | KW40 | KW42 | KW44 | KW46 | KW48 | KW50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 Zwischenpräsentation 1 | 19.10.2026 | | | | | | | |
| M2 Zwischenpräsentation 2 | 16.11.2026 | | | | | | | |
| M3 Scope-Freeze | 04.12.2026 | | | | | | | |
| M4 Zwischenpräsentation 3 | 14.12.2026 | | | | | | | |
| M5 Abgabe | 18.12.2026 | | | | | | | |

Die Tabelle wird zweiwöchentlich nachgeführt. Verschiebt sich ein erwarteter Termin, wird die Ursache im Statusbericht derselben Woche festgehalten.

#### Fortschrittsmessung

Gemessen wird am Verhältnis abgeschlossener zu geplanter Story Points im laufenden Sprint. Teilweise erledigte Stories zählen nicht, eine Story ist erledigt oder nicht. Zusätzlich wird pro Sprint der Anteil erfüllter Erfolgskriterien aus Kapitel 1.5 ausgewiesen, damit Fortschritt nicht nur als Aktivität, sondern als Zielerreichung sichtbar wird.

### 2.14 Änderungsmanagement

Merkblatt A verlangt für grössere Projektänderungen, etwa neue Ziele oder einen neuen Fokus, die Zustimmung beider Experten. Dafür gilt folgender Ablauf:

1. Der Änderungsbedarf wird im Projektjournal mit Datum und Anlass festgehalten
2. Ein Change Request wird erstellt mit Anlass, betroffenem Ziel, Auswirkung auf Umfang, Termine und Aufwand, geprüften Alternativen und Empfehlung
3. Der Change Request geht an beide Experten, mit einer Frist von fünf Arbeitstagen vor dem gewünschten Wirksamwerden
4. Die Zustimmung beider Experten wird schriftlich im Teams-Kanal eingeholt
5. Der Entscheid wird in der folgenden Tabelle und im Statusbericht der laufenden Woche dokumentiert
6. Backlog, Terminplan und die Zieltabelle in Kapitel 1.4 werden nachgeführt

| ID | Datum | Anlass | Änderung | Auswirkung | Entscheid | Zustimmung |
| --- | --- | --- | --- | --- | --- | --- |
| CR-01 | | | | | | |

Nicht jede Anpassung ist ein Change Request. Die Priorisierung innerhalb des bewilligten Umfangs, das Verschieben einer Story zwischen Sprints und technische Detailentscheide liegen in der Verantwortung des Diplomanden und werden im Journal beziehungsweise als Architekturentscheid dokumentiert.

### 2.15 Risikomanagement

Das Risikomanagement folgt dem Zyklus Identifikation, Bewertung, Steuerung und Überwachung. Bewertet wird mit Eintrittswahrscheinlichkeit und Auswirkung auf einer Skala von 1 bis 5. Der Risikowert ist das Produkt beider Grössen.

#### Bewertungsskalen

Für beide Bewertungsgrössen gilt dieselbe fünfstufige Skala.

| Stufe | Eintrittswahrscheinlichkeit | Auswirkung auf das Projekt |
| --- | --- | --- |
| 1 | Sehr unwahrscheinlich, kein Anhaltspunkt | Vernachlässigbar, kein Einfluss auf Ziele oder Termine |
| 2 | Unwahrscheinlich, in Einzelfällen denkbar | Gering, interne Umplanung genügt |
| 3 | Möglich, schon einmal vorgekommen | Spürbar, ein Sprintziel ist gefährdet |
| 4 | Wahrscheinlich, mit Aufwand vermeidbar | Schwer, ein Meilenstein ist gefährdet |
| 5 | Sehr wahrscheinlich, tritt ohne Gegenmassnahme ein | Kritisch, ein Erfolgskriterium ist gefährdet |

Aus dem Produkt beider Stufen ergibt sich der Risikowert zwischen 1 und 25. Er bestimmt die Einstufung und die daraus abgeleitete Handlung.

| Risikowert | Einstufung | Handlung |
| --- | --- | --- |
| 1 bis 5 | Gering | Akzeptieren, im Statusbericht beobachten |
| 6 bis 11 | Mittel | Massnahme definieren und umsetzen |
| 12 bis 25 | Hoch | Massnahme sofort umsetzen, Firmenexperte informieren, wöchentlich überprüfen |

#### Risikoregister

Die Risiken R01 bis R05 stammen aus der bewilligten Projektbeschreibung. R06 bis R11 wurden bei der Projektinitialisierung ergänzt. Zu jedem Risiko sind eine Strategie, ein Frühwarnindikator und eine Massnahme festgelegt, damit erkennbar bleibt, woran ein Eintreten frühzeitig sichtbar wird.

| ID | Risiko | EW | AW | Wert | Strategie | Frühwarnindikator | Massnahme |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | Technische Komplexität der Kombination aus Kubernetes, KubeVirt, Zustandsführung, MCP und Public Cloud | 4 | 4 | 16 | Vermindern | Eine Story aus E6 oder E7 überschreitet ihre Schätzung um mehr als das Doppelte | Frühe Smoke-Tests auf beiden Zielplattformen, Verzicht auf optionale Erweiterungen zugunsten des vollständigen Lebenszyklus, Zeitbox von zwei Arbeitseinheiten pro Blockade mit anschliessendem Entscheid über einen Alternativweg |
| R02 | Cloud-Ressourcen und Kosten: ungenügende Quotas, eingeschränkte Dienstverfügbarkeit oder unerwartete Kosten | 3 | 3 | 9 | Vermindern | Quota-Fehlermeldung beim Smoke-Test, Budgetwarnung über 50 Prozent | Quotas und Dienste im Cloud-Smoke-Test in Sprint 1 prüfen, Budgetwarnungen bei CHF 25 und CHF 40, Ressourcen minimal halten, nach jedem Test sofort löschen |
| R03 | Zeitmanagement: der Umfang überschreitet die verfügbare Projektzeit | 4 | 5 | 20 | Vermindern | Velocity liegt in zwei aufeinanderfolgenden Wochen mehr als 25 Prozent unter Plan | Verbindlich begrenzter Kernumfang, eine technisch reduzierte Test-Lernumgebung, Scope-Freeze am 04.12.2026, festgelegte Reihenfolge der Umfangsreduktion, reservierte Abschlusszeit |
| R04 | Netzwerk und Berechtigungen: fehlende Freigaben verzögern die Anbindung der Zielplattformen | 2 | 4 | 8 | Vermindern | Eine benötigte Verbindung ist beim ersten Test nicht erreichbar | Zugang über WireGuard und lerncloud-Schlüssel in der ersten Projektwoche verifiziert. Änderungen an produktiven Netzwerken bleiben ausserhalb des Umfangs |
| R05 | Unvollständiger Teardown und Zustandsabweichungen: nach delete bleiben Ressourcen zurück oder der gespeicherte Zustand weicht vom tatsächlichen ab | 3 | 3 | 9 | Vermindern | Ein Lauf findet nach delete noch zugeordnete Ressourcen | Wiederholbare Operationen, Statusprüfung vor und nach jeder Aktion, eindeutige Laufkennzeichnung aller Ressourcen, automatisierter Cleanup-Test mit Warten auf den Endzustand |
| R06 | Hardwareausfall im HF-Labor | 2 | 3 | 6 | Vermindern | Ein Knoten erscheint nach einem Neustart nicht mehr | Clusteraufbau und Konfiguration reproduzierbar dokumentiert, zweites KubeVirt-System auf kvcontrol als Ausweichumgebung |
| R07 | Verfügbarkeit der Experten: Termine für Zwischenpräsentationen lassen sich nicht rechtzeitig vereinbaren | 2 | 3 | 6 | Vermindern | Keine Terminbestätigung 10 Arbeitstage vor dem geplanten Termin | Alle drei Termine beim Kickoff fixieren und in die Kalender legen, Ersatztermin in derselben Woche vorschlagen |
| R08 | Dokumentationsrückstand: die Dokumentation wird erst am Projektende nachgezogen | 3 | 4 | 12 | Vermeiden | Ein Issue erreicht Done ohne zugehörigen Dokumentationsabschnitt | Dokumentationsabschnitt ist Teil der Definition of Done, eigene Doku-Ampel im Statusbericht, Doku-Stand ist fester Punkt jeder Retrospektive |
| R09 | Reifegrad und Änderungen im MCP-Umfeld | 3 | 3 | 9 | Vermindern | Ein verwendetes Werkzeug meldet inkompatible Änderungen | Verwendete Versionen früh festschreiben, Adapterschnittstelle schmal halten, Rückfallweg über direkte API-Aufrufe vorsehen und als Erkenntnis dokumentieren |
| R10 | Persönliche Kapazität: Krankheit oder beruflicher Engpass reduziert die verfügbare Zeit | 3 | 4 | 12 | Vermindern | Zwei aufeinanderfolgende Wochen unter 8 Stunden Projektzeit | Wochenkapazität im Journal erfassen, bei Unterschreitung sofort Umfangsreduktion einleiten und den Firmenexperten informieren |
| R11 | Verlust des Remote-Zugangs zu den Zielsystemen nach Neustart oder Netzwerkänderung | 3 | 4 | 12 | Vermeiden | Eine Maschine ist nach einem Neustart über WireGuard nicht mehr erreichbar | Keine Netzwerkänderungen und keine Neustarts der Zielsysteme ohne Absprache, Arbeiten bevorzugt am Labortag vor Ort, zweites System als Ausweichweg |

Die Strategien beschränken sich auf Vermindern und Vermeiden. Ein Übertragen an Dritte oder ein bewusstes Akzeptieren kommt in diesem Projekt nicht vor, weil der Diplomand alle Risiken selbst trägt und keines der elf Risiken so gering bewertet ist, dass darauf verzichtet werden könnte.

#### Risikomatrix

Die Matrix ordnet alle elf Risiken nach Auswirkung und Eintrittswahrscheinlichkeit ein. Die Zahlen bezeichnen die Risiko-IDs.

| Auswirkung / Eintrittswahrscheinlichkeit | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 5 kritisch | | | | R03 | |
| 4 schwer | | R04 | R08, R10, R11 | R01 | |
| 3 spürbar | | R06, R07 | R02, R05, R09 | | |
| 2 gering | | | | | |
| 1 vernachlässigbar | | | | | |

| Einstufung | Risiken |
| --- | --- |
| Hoch, Wert 12 bis 25 | R01, R03, R08, R10, R11 |
| Mittel, Wert 6 bis 11 | R02, R04, R05, R06, R07, R09 |
| Gering, Wert 1 bis 5 | Keine |

Fünf der elf Risiken sind hoch eingestuft. Die drei höchstbewerteten Risiken R03, R01 und R10 gehen auf dieselbe Ursache zurück: auf die knappe Zeit im Verhältnis zur technischen Unsicherheit. Sie werden deshalb mit derselben Gegenmassnahme gesteuert, nämlich einem verbindlich begrenzten Kernumfang mit vorab festgelegter Reihenfolge der Umfangsreduktion.

#### Verlauf der Risikobewertung

Die Bewertung wird an jedem Sprintende überprüft. Veränderungen werden hier und im Statusbericht der betreffenden Woche ausgewiesen.

| Risiko | Start | Ende Sprint 1 | Ende Sprint 2 | Ende Sprint 3 | Bemerkung |
| --- | --- | --- | --- | --- | --- |
| R01 | 16 | | | | |
| R02 | 9 | | | | |
| R03 | 20 | | | | |
| R04 | 8 | | | | Bereits in Woche 1 von 12 auf 8 gesenkt, da der Zugang verifiziert ist |
| R05 | 9 | | | | |
| R06 | 6 | | | | |
| R07 | 6 | | | | |
| R08 | 12 | | | | |
| R09 | 9 | | | | |
| R10 | 12 | | | | |
| R11 | 12 | | | | |

Die Spalte Start hält den Wert aus der Erstbewertung fest. R04 ist bereits vor Sprint 1 abgesunken, weil der Zugang zu den Zielsystemen verifiziert werden konnte. Die übrigen Werte werden erstmals am Ende von Sprint 1 überprüft.

#### Eingetretene Risiken

Tritt ein Risiko ein, wird es mit Datum, Wirkung und Reaktion in der folgenden Tabelle festgehalten. Die Tabelle ist zu Projektbeginn leer und wird bei Bedarf ergänzt.

| ID | Datum | Was ist eingetreten | Wirkung | Reaktion | Ergebnis |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

### 2.16 Wirtschaftlichkeitsbetrachtung

Merkblatt A verlangt eine Bewertung des Projekts hinsichtlich Kosten-Nutzen, Ressourcen, Nachhaltigkeit und Skalierbarkeit. Die Betrachtung selbst erfolgt in Kapitel 6. Die Methode wird hier festgelegt, damit die dafür nötigen Daten von Beginn weg erhoben werden.

| Betrachtungsfeld | Datenquelle | Erhebung ab |
| --- | --- | --- |
| Aufwand heutiges Vorgehen | Ausgangsmessung, Bereitstellungszeit und manuelle Eingriffe pro Lernumgebung | Sprint 1, US10 |
| Aufwand Proof of Concept | Messprotokolle der sechs Durchläufe | Sprint 3, US27 und US28 |
| Einmalaufwand | Erfasste Projektstunden für Aufbau und Entwicklung | Laufend über das Journal |
| Direkte Kosten | Cloud-Verbrauch, maximal CHF 50, keine Beschaffung | Sprint 1, Budgetwarnung |
| Nutzen, quantitativ | Eingesparte Bereitstellungszeit pro Lernumgebung, hochgerechnet auf die Zahl der Umgebungen pro Semester | Sprint 3 |
| Nutzen, qualitativ | Reduzierte Personenabhängigkeit, Reproduzierbarkeit, Wiederverwendbarkeit | Sprint 3 |
| Nachhaltigkeit | Ressourcenverbrauch, vollständiger Abbau nach Nutzung statt dauerhaft laufender Umgebungen | Sprint 3 |
| Skalierbarkeit | Aufwand für eine zusätzliche Lernumgebung und für eine zusätzliche Zielplattform | Sprint 3, qualitativ begründet |

Entscheidend für die Aussagekraft der Betrachtung ist die Ausgangsmessung in Sprint 1. Ohne einen belegten Ausgangswert für das heutige Vorgehen liesse sich der spätere Vergleich nicht quantifizieren.

Die Bewertung der MCP-basierten Adapterarchitektur gegenüber einer direkten API-Anbindung erfolgt als Nutzwertanalyse über die fünf in der Projektbeschreibung festgelegten Kriterien: Kopplung, Aufwand, Testbarkeit, Fehlerbehandlung und Erweiterbarkeit. Die Gewichtung der Kriterien wird vor der Bewertung festgelegt und begründet, damit sie nachvollziehbar bleibt und nicht nachträglich an das Ergebnis angepasst wird.

### 2.17 Projektjournal

Das Projektjournal wird fortlaufend geführt und hält zentrale Ereignisse, Entscheide, Beobachtungen und Reflexionen fest. Es liegt unter `docs/journal/`, ein File pro Monat, und ist über GitHub Pages jederzeit einsehbar.

Ein Journaleintrag entsteht pro Arbeitseinheit und enthält Datum, Dauer, bearbeitete Issues, wesentliche Beobachtungen, getroffene Entscheide und offene Punkte. Das Journal ersetzt in diesem Einzelprojekt das Daily Scrum und dient zugleich als Grundlage für die Aufwandserfassung in der Wirtschaftlichkeitsbetrachtung.

Sackgassen und Fehlversuche werden bewusst festgehalten. Sie sind Teil der Lösungsfindung und liefern das Material für die Reflexion in Kapitel 9.

### 2.18 Lehren aus den Semesterarbeiten 4 und 5

Die Projektführung dieser Arbeit baut auf den Rückmeldungen der Bewertungen der Semesterarbeiten 4 und 5 auf.

| Rückmeldung aus der Bewertung | Konsequenz in dieser Arbeit | Wo verankert |
| --- | --- | --- |
| Viele Änderungen kamen auf den letzten Drücker | Scope-Freeze am 04.12.2026, ab da nur noch Tests, Messungen und Dokumentation | Meilenstein M3, Kapitel 2.6 |
| Das Project Board war auf privat gestellt und nicht zugänglich | Board und Repository öffentlich, Zugriff in Sprint 1 verifiziert und im Statusbericht KW38 bestätigt | Kapitel 2.4, US02 |
| Die Dozenten hatten lange keine Information über den Projektstand | Wöchentlicher Statusbericht ab KW38, Ampelsystem, Standblock auf der Startseite | Kapitel 2.13 |
| Sprints waren unterschiedlich lang | Sprintlängen folgen den fixen Reviewterminen, die Ungleichheit ist begründet, die Planung erfolgt über ein konstantes Wochenbudget | Kapitel 2.6.1 und 2.9 |
| Sprintziele waren verbesserungswürdig | Sprintziel als ein Satz Outcome, mit Abgleich gegen die Zieltabelle im Review | Kapitel 2.7 |
| Die Schätzung der Tasks war zu Beginn unklar | Schätzskala mit Referenzstory US01, Wochenbudget, Velocity-Verfolgung | Kapitel 2.9 |
| Die Dokumentation war lange mager und bestand vor allem aus Tabellen | Dokumentation laufend, Fliesstext mit Begründung statt reiner Tabellen, Doku-Ampel im Statusbericht | Kapitel 2.13 |
| Demo und Use Case waren nicht optimal vorbereitet | Demo-Skript mit Backup-Plan, Generalprobe am Vortag jeder Zwischenpräsentation | US37, Kapitel 2.7 |
| Tests und Lint wurden in einer Zwischenpräsentation nicht nachvollziehbar erklärt | Für jeden Präsentationsblock wird vorab eine Erklärung in drei Sätzen vorbereitet, die Teststrategie ist schriftlich begründet | Kapitel 2.12 |
| Zusammenarbeit und Fremdfeedback waren im Repository nur begrenzt sichtbar | Reviewprotokolle mit Expertenrückmeldungen und deren Umsetzung als Issues | Kapitel 2.7 und 8 |
| Abzug für schwarzen Folienhintergrund | Heller Foliensatz, an das TBZ-Layout angelehnt | US37 |

Die Rückmeldungen betreffen überwiegend die Projektführung und die Nachweisführung, weniger die technische Umsetzung. Die daraus abgeleiteten Massnahmen sind deshalb nicht als Absichtserklärung formuliert, sondern jeweils an einen Meilenstein, eine User Story oder ein Kapitel dieser Dokumentation gebunden und dort überprüfbar.

## 3 Analyse und Konzept

### 3.1 Ausgangslage der Infrastruktur

Vor der Umsetzung wurde erhoben, welche Infrastruktur tatsächlich zur Verfügung steht. Die Erhebung erfolgte am 14.09.2026, dem ersten Projekttag, mit einem rein lesenden Auditlauf über beide freigegebenen Systeme. Die vollständigen Ausgaben liegen unter `docs/nachweise/`.

#### 3.1.1 Freigegebene Hardware

Die Freigabe erfolgte am 14.09.2026 durch die HF-Lehrgangsleitung und umfasst den Server DL380-01, fünf HP-Rechner und einen eigenen Switch im Netz 10.0.26.0/24.

| System | Hostname | CPU | Arbeitsspeicher | Datenträger | Rolle im Projekt |
| --- | --- | --- | --- | --- | --- |
| HP DL380 | `dl380-01` | Intel Xeon E5-2620 v3, 24 logische Kerne | 125 GB, davon 121 GB frei | 1,7 TB, davon 1,6 TB frei | Zielplattform für die Umsetzung |
| HP Terra | `kvcontrol` | Intel Core i7-9700T, 8 Kerne | 15 GB, davon 12 GB frei | 238 GB NVMe, davon 184 GB frei | Zweitsystem und Ausweichumgebung |
| HP Terra, vier weitere | noch nicht in Betrieb genommen | | | | Reserve, im Proof of Concept nicht benötigt |

Beide Systeme laufen unter Ubuntu 24.04.4 LTS. Der Unterschied im Arbeitsspeicher ist für dieses Projekt wesentlich und bildet in ADR-001 das ausschlaggebende Kriterium.

#### 3.1.2 Zugang und Netzwerk

Der Zugriff erfolgt über eine WireGuard-Verbindung in das HF-Labor-Netz und anschliessend über SSH mit dem lerncloud-Schlüssel. Beide Systeme sind WireGuard-Clients mit je einem Peer, dem Gateway. Die drei Interfaces bilden die drei Klassennetze des HF-Labors ab.

```text
--- Netzwerk dl380-01 ---
eno1             UP             10.0.21.197/24
wg1.24           UNKNOWN        10.1.24.5/24
wg2.24           UNKNOWN        10.2.24.5/24
wg3.24           UNKNOWN        10.3.24.5/24
default via 10.0.21.1 dev eno1 proto dhcp src 10.0.21.197
```

Die Haupt-Netzwerkkarte hängt im allgemeinen Netz 10.0.21.0/24, die Verwaltung erfolgt über 10.1.24.5. Die Schnittstellen `eno2` bis `eno4` sind vorhanden, aber nicht aktiv. Der freigegebene Switch im Netz 10.0.26.0/24 ist zum Zeitpunkt der Erhebung noch nicht angebunden.

Daraus ergibt sich ein Risiko: Der Fernzugriff auf beide Systeme hängt an der WireGuard-Verbindung, die auf denselben Maschinen terminiert. Ein Neustart oder eine Änderung der Netzwerkkonfiguration kann den eigenen Zugang unterbrechen. Dieser Sachverhalt ist als Risiko R11 in Kapitel 2.15 erfasst.

#### 3.1.3 Vorgefundener Zustand auf dl380-01

Auf dem Zielsystem lief bei Projektbeginn bereits eine vollständige Plattform.

```text
NAME       STATUS   ROLES                  AGE   VERSION   INTERNAL-IP    CONTAINER-RUNTIME
dl380-01   Ready    control-plane,master   20d   v1.35.6   10.0.21.197    containerd://2.1.6
```

| Komponente | Zustand |
| --- | --- |
| MicroK8s | v1.35.6, Einzelknoten, nicht hochverfügbar, eingerichtet am 25.08.2026 |
| Netzwerk im Cluster | Calico |
| Aktivierte Erweiterungen | dns, ha-cluster, helm, helm3, hostpath-storage, metrics-server, rbac, cert-manager |
| KubeVirt | v1.9.0, Zustand `Deployed`, inklusive Export-Proxy und Vorlagenverwaltung |
| CDI, Containerized Data Importer | vorhanden, vier Komponenten aktiv |
| Kommandozeilenwerkzeug | `virtctl` unter `/usr/local/bin/virtctl` |
| Virtualisierung auf dem Host | `vmx` vorhanden, Kernelmodul `kvm_intel` geladen, keine aktive Nutzung |
| Laufende virtuelle Maschinen | keine |
| Fachliche Arbeitslasten | keine |

```text
--- KubeVirt Phase ---
Deployed  Version: v1.9.0

--- StorageClasses ---
NAME                          PROVISIONER                    RECLAIMPOLICY   VOLUMEBINDINGMODE
local-storage                 kubernetes.io/no-provisioner   Delete          Immediate
microk8s-hostpath (default)   microk8s.io/hostpath           Delete          WaitForFirstConsumer
```

Nicht vorhanden sind ein Ingress-Controller und ein Load-Balancer. Die Erreichbarkeit von Diensten muss deshalb über andere Mechanismen gelöst werden, siehe ADR-002.

#### 3.1.4 Zweitsystem kvcontrol

Auf `kvcontrol` läuft ein eigenständiges, vom Zielsystem getrenntes MicroK8s derselben Version, eingerichtet am 28.07.2026, ebenfalls mit KubeVirt und CDI, jedoch ohne cert-manager, Export-Proxy und Vorlagenverwaltung. Auch dieses System ist leer.

Der Name des Hosts legt nahe, dass er ursprünglich als Steuerknoten für eine KubeVirt-Umgebung vorgesehen war. Für diese Arbeit dient er als Ausweichumgebung, falls das Zielsystem ausfällt oder durch einen Fehler unbrauchbar wird. Damit ist Risiko R06 abgedeckt, ohne dass zusätzliche Hardware in Betrieb genommen werden muss.

#### 3.1.5 Einordnung der übernommenen Vorarbeit

Der Kubernetes-Cluster und die KubeVirt-Installation auf beiden Systemen waren bei Projektbeginn bereits vorhanden und sind nicht Eigenleistung dieser Arbeit. Die Einrichtungsdaten, 28.07.2026 und 25.08.2026, liegen vor dem Projektstart am 14.09.2026 und sind im Cluster nachvollziehbar.

Die bewilligte Projektbeschreibung verlangt, dass übernommene Vorarbeiten nachvollziehbar dokumentiert werden. Diese Kennzeichnung erfüllt diese Anforderung.

Die Eigenleistung dieser Arbeit beginnt oberhalb dieser Plattform und umfasst:

- die Verifikation und Dokumentation des vorgefundenen Zustands
- das plattformneutrale Fachmodell und dessen Validierung
- den Agenten mit Zustandsführung
- die MCP-basierte Adapterschicht für beide Zielplattformen
- die Messung, den Vergleich und die Bewertung

Der Umstand, dass die Plattform bereitstand, verändert den Umfang der Arbeit gegenüber der bewilligten Projektbeschreibung nicht. Er verschiebt lediglich Aufwand von der Einrichtung zur Verifikation. Die betroffenen User Stories US12 und US13 wurden entsprechend von fünf und drei auf je zwei Story Points reduziert, die frei gewordene Kapazität floss in US38 und in die Messvorbereitung.

#### 3.1.6 Architekturentscheide aus der Erhebung

Aus dem vorgefundenen Zustand ergeben sich drei Entscheide, die vor der Umsetzung getroffen werden mussten.

**ADR-001: dl380-01 als Zielplattform**

| | |
| --- | --- |
| Status | Entschieden am 14.09.2026 |
| Kontext | Zwei gleichwertig eingerichtete KubeVirt-Umgebungen stehen zur Verfügung |
| Entscheid | Die Umsetzung erfolgt auf `dl380-01`, `kvcontrol` dient als Ausweichumgebung |

Begründung:

| Kriterium | dl380-01 | kvcontrol | Gewicht |
| --- | --- | --- | --- |
| Freier Arbeitsspeicher | 121 GB | 12 GB | Hoch. Virtuelle Maschinen belegen Arbeitsspeicher exklusiv. Die Test-Lernumgebung leitet sich aus Modulprofilen mit mehreren Maschinen ab |
| Freier Speicherplatz | 1,6 TB | 184 GB | Hoch. Jede importierte Maschine belegt mehrere Gigabyte, sechs Durchläufe summieren sich |
| Logische Kerne | 24 | 8 | Mittel |
| Vollständigkeit der Installation | Export-Proxy, Vorlagen, cert-manager | Grundinstallation | Niedrig |

Verworfene Alternative: Zusammenschluss beider Systeme zu einem Cluster mit zwei Knoten. Ein Mehrknoten-Cluster ist in der bewilligten Projektbeschreibung ausdrücklich dem Ausblick zugeordnet und nicht Teil des Umfangs. Zudem würde der Zusammenschluss Eingriffe in die Netzwerkkonfiguration erfordern, die den Fernzugriff gefährden.

**ADR-002: NodePort für die Erreichbarkeit des Testdienstes**

| | |
| --- | --- |
| Status | Entschieden am 14.09.2026 |
| Kontext | Der Readiness-Check muss den Testdienst in der virtuellen Maschine automatisiert erreichen. Auf dem Cluster sind weder ein Ingress-Controller noch ein Load-Balancer vorhanden |
| Entscheid | Der Testdienst wird über einen Service vom Typ NodePort erreichbar gemacht |

Geprüfte Alternativen:

| Weg | Bewertung |
| --- | --- |
| NodePort | Gewählt. Standardmittel von Kubernetes, keine Änderung an der Plattform nötig, aus dem Verwaltungsnetz direkt erreichbar, vom Adapter mit wenigen Zeilen erzeugbar |
| Weiterleitung über `virtctl port-forward` | Verworfen. Für manuelle Arbeit geeignet, für einen automatisierten Check jedoch umständlich, weil der Agent einen Prozess offen halten müsste |
| Multus mit Netzwerkbrücke, Maschine erhält eine Adresse im Labornetz | Verworfen für den Proof of Concept. Am nächsten an einer produktiven Lernumgebung, erfordert aber Eingriffe in die Netzwerkkonfiguration des Systems, das den Fernzugriff trägt. Wird im Ausblick in Kapitel 10 als produktionsnaher Weg behandelt |

**ADR-003: microk8s-hostpath als Speicherklasse**

| | |
| --- | --- |
| Status | Entschieden am 14.09.2026 |
| Kontext | Zwei Speicherklassen stehen zur Verfügung |
| Entscheid | Virtuelle Maschinen verwenden `microk8s-hostpath` |

Begründung: `local-storage` verwendet den Provisioner `kubernetes.io/no-provisioner` und legt keine Datenträger selbst an. Jede virtuelle Maschine würde damit ein von Hand erstelltes PersistentVolume benötigen. Solche manuellen Schritte sollen durch diese Arbeit entfallen. `microk8s-hostpath` ist die Standardklasse des Clusters, legt Datenträger bei Bedarf an und entfernt sie beim Löschen wieder.

Einschränkung, die bewusst in Kauf genommen wird: `microk8s-hostpath` bindet Daten an einen einzelnen Knoten. Für einen Einzelknoten-Cluster ist das folgenlos, für einen späteren Mehrknoten-Betrieb wäre verteilter Speicher nötig. Das ist in Kapitel 10 vermerkt.

#### 3.1.7 Umgebung der Ausgangsmessung

Die heutige Bereitstellung über LernMAAS läuft nicht auf `dl380-01`, sondern auf einer eigenen, davon vollständig getrennten Anlage. Diese wurde am 14.09.2026 lesend erhoben.

**Aufbau der Anlage**

Fünf Racks, je ein eigenes Netz und ein eigener MAAS-Controller:

| Rack | Netz | MAAS-Controller | KVM-Hosts |
| --- | --- | --- | --- |
| rack-au-01 | 10.0.41.0/24 | `cloud-au-2` | `cloud-au-03` bis `cloud-au-08` |
| rack-au-02 | 10.0.42.0/24 | `cloud-au-09` | `cloud-au-10` bis `cloud-au-15` |
| rack-au-03 | 10.0.43.0/24 | `cloud-au-16` | `cloud-au-17` bis `cloud-au-22` |
| rack-au-04 | 10.0.44.0/24 | `cloud-au-23` | `cloud-au-24` bis `cloud-au-29` |
| rack-au-05 | 10.0.45.0/24 | `cloud-au-30` | `cloud-au-31` bis `cloud-au-36` |

Je Rack sieben Maschinen, ein Controller und sechs Virtualisierungshosts. Die Controller-Namen wurden auf allen fünf Racks direkt abgefragt, die Zuordnung der Hosts ist für Rack 5 geprüft und für die übrigen aus dem durchgehenden Siebenerabstand abgeleitet.

Insgesamt bestehen damit fünf eigenständige MAAS-Installationen, 30 Virtualisierungshosts und 20 VPN-Umgebungen. Eine übergeordnete Steuerung über die Racks hinweg besteht nicht, jedes Rack wird eigenständig betrieben.

**Hardware**

Stellvertretend `cloud-au-31`:

| Merkmal | Wert |
| --- | --- |
| Modell | HP ProDesk 600 G1 SFF |
| CPU | Intel Core i7-4790, 8 Kerne |
| Arbeitsspeicher | 32 GiB |
| Datenträger | 1 TB, ein Datenträger |
| Betriebssystem | Ubuntu 22.04 LTS |
| Firmware | L01 v02.77 vom 17.04.2019, Boot-Modus PXE |
| Stromsteuerung in MAAS | Manual |

Der letzte Punkt ist für die Bewertung des heutigen Verfahrens wesentlich: MAAS kann diese Maschinen nicht selbst ein- und ausschalten. Für die virtuellen Maschinen gilt das nicht, sie werden über `Virsh` gesteuert. Automatisiert steuerbar sind damit die virtuellen Maschinen, nicht aber die physischen Systeme, auf denen sie laufen.

**Netz- und Zonenmodell**

Je Rack existiert in MAAS genau ein Subnetz, für Rack 5 also `10.0.45.0/24` mit MAAS-eigenem DHCP und 62 Prozent freien Adressen. Die vier VPN-Umgebungen eines Racks sind keine eigenen Subnetze, sondern Availability Zones nach dem Namensschema `10-<VPN>-<Rack>-0`. Alle Maschinen liegen im selben Subnetz; die Trennung nach VPN erfolgt ausserhalb von MAAS auf dem Gateway.

Belegung in Rack 5 zum Erhebungszeitpunkt:

| Zone | Maschinen |
| --- | --- |
| `10-1-45-0` | 0 |
| `10-2-45-0` | 0 |
| `10-3-45-0` | 0 |
| `10-4-45-0` | 24 |
| `default` | 6 Hosts, 1 Controller |

Für die Ausgangsmessung wird die Zone `10-1-45-0` verwendet. Sie ist nachweislich leer, und die Zuordnung macht jederzeit unterscheidbar, welche Objekte aus dieser Arbeit stammen.

**Abweichung zwischen Reservationsliste und Systemzustand**

Die zentrale Reservationsliste weist für Rack 5 alle vier Umgebungen als frei aus. In MAAS stehen jedoch 24 bereitgestellte Maschinen des Moduls m437 mit dem Merkmal `m437-ICT23d` in der Zone `10-4-45-0`, die meisten davon eingeschaltet, mit Ubuntu 24.04 LTS und Adressen von 10.0.45.75 aufwärts.

Ob diese Umgebung derzeit im Unterricht verwendet wird, ist für diesen Befund nicht massgeblich. Massgeblich ist, dass die Liste sie in keinem der beiden Fälle führt: weder als belegt noch als abgeräumt. Die Belegung der Umgebungen wird damit ausserhalb des Systems geführt, und der geführte Stand weicht vom tatsächlichen ab. Dieser Punkt wird in Kapitel 3.2.7 als Befund B8 aufgenommen.

**Umgang mit Zugangsdaten**

Die WireGuard-Konfigurationen der Umgebungen liegen als base64-kodiertes Archiv im Beschreibungsfeld der jeweiligen Availability Zone und enthalten private Schlüssel. Diese Dokumentation beschreibt den Mechanismus, gibt aber keine Inhalte wieder. Gleiches gilt für Anmeldedaten der Oberfläche und für die Klartextangaben in den cloud-init-Vorlagen des öffentlichen lerncloud-Projekts.

**Gegenüberstellung**

| Merkmal | LernMAAS-Umgebung | Zielplattform dieser Arbeit |
| --- | --- | --- |
| Hardware | HP ProDesk 600 G1, i7-4790, 8 Kerne, 32 GiB | HP DL380, Xeon E5-2620 v3, 24 Kerne, 125 GB |
| Bereitstellung | MAAS mit `createvms`, Konfigurationsdatei, Shellskripte, Oberfläche | Kubernetes mit KubeVirt |
| Steuerung | fünf getrennte Controller | ein Cluster |
| Netzzuordnung | Availability Zones je VPN | Namensraum und Label |

Der Unterschied in der Hardware ist erheblich und begründet die Trennung der Messgrössen in Kapitel 3.4.

### 3.2 IST-Analyse der heutigen Bereitstellung

#### 3.2.1 Beteiligte Komponenten

| Komponente | Aufgabe |
| --- | --- |
| MAAS | Verwaltung der Maschinen, DHCP, PXE, Installation des Betriebssystems |
| `config.yaml` | Zentrale Beschreibung aller Modulprofile, Grösse und Dienste der virtuellen Maschinen |
| `createvms` | Legt Resource Pool und virtuelle Maschinen anhand eines Profils an |
| `updateaz` | Erzeugt WireGuard-Schlüssel und legt sie in der Availability Zone ab |
| cloud-init | Erstkonfiguration beim ersten Start, bindet Dienste und Modul-Repositories ein |
| Modul-Repositories | Je Modul ein eigenes Repository mit Installationsskripten und Anleitung |
| Reservationsliste | Tabelle, in der die Belegung der VPN-Umgebungen von Hand geführt wird |

#### 3.2.2 Die zentrale Konfigurationsdatei

Die `config.yaml` beschreibt 28 Modulprofile. Sie ist die fachliche Beschreibung der heutigen Lernumgebungen und wird laut ihrem eigenen Kopfkommentar sowohl von cloud-init als auch von allen Hilfsskripten verwendet.

Die drei für diese Arbeit massgeblichen Profile:

| Feld | m239 | m254 | m426 |
| --- | --- | --- | --- |
| `vm.storage` | 8 | 12 | 8 |
| `vm.memory` | 2048 | 2048 | 3584 |
| `vm.cores` | 2 | 2 | 2 |
| `vm.count` | 24 | 20 | 6 |
| `services.nfs` | true | true | true |
| `services.docker` | false | false | true |
| `services.k8s` | leer | k3s | minimal |
| `services.wireguard` | use | use | use |
| `services.ssh` | generate | generate | generate |
| `services.samba` | true | false | false |
| `services.firewall` | false | false | false |
| `repositories` | tbz-it/M239 | tbz-it/M254 | tbz-it/M426 |

Daraus lässt sich die fachliche Struktur der heutigen Beschreibung ablesen: Grösse der Maschine, Anzahl, ein Satz von Diensten als Schalter und ein Verweis auf ein Modul-Repository.

Für die Einordnung ist wesentlich, dass eine deklarative Beschreibung der Lernumgebungen heute bereits existiert. Die vorliegende Arbeit erfindet sie nicht, sondern setzt an ihren Grenzen an. Diese sind:

| Merkmal | heutige `config.yaml` | Fachmodell dieser Arbeit |
| --- | --- | --- |
| Deklarativ | ja | ja |
| Gegen ein Schema prüfbar | nein, Auswertung über einen Textparser im Skript | ja, JSON Schema |
| Plattformneutral | nein, die Felder zielen auf `maas pod compose` | ja |
| Dienste | boolesche Schalter, umgesetzt in Shellskripten | fachlich beschriebener Zielzustand mit prüfbarem Readiness-Kriterium |
| Zustandsführung | keine | create, status, reset, delete über festgelegte Zustandsübergänge |
| Abbau | nicht Teil der Beschreibung | Teil des Lebenszyklus, mit Nachweis |

#### 3.2.3 Verteilung der Konfiguration

Jeder der fünf Controller hält eine eigene Kopie der `config.yaml` in einem lokalen Git-Arbeitsverzeichnis. Eine Prüfung über alle fünf Racks ergab dieselbe Prüfsumme `965e401d…` und denselben Commit `1f105a7` vom 31.12.2025.

Die Kopien sind damit inhaltsgleich. Zugleich zeigen unterschiedliche Änderungszeitpunkte der Dateien, dass sie zu verschiedenen Zeiten einzeln nachgezogen wurden. Der Befund lautet deshalb nicht, dass die Konfigurationen auseinanderlaufen, sondern dass die Übereinstimmung organisatorisch hergestellt und nicht durch einen technischen Mechanismus gesichert wird. Eine Änderung an einem Modulprofil muss auf fünf Maschinen einzeln wirksam gemacht werden, und im System ist nicht feststellbar, ob das geschehen ist.

#### 3.2.4 Das Skript `createvms`

Der Aufruf lautet `createvms <config.yaml> <Modul> <Anzahl> <Suffix> <Offset>`. Das Skript liest das Profil, legt bei Bedarf einen Resource Pool an und erzeugt über `maas pod compose` virtuelle Maschinen, gleichmässig auf die Virtualisierungshosts verteilt.

Drei Eigenschaften sind für diese Arbeit wesentlich:

Es entsteht keine nutzbare Lernumgebung. Nach dem Lauf stehen die Maschinen im Zustand `Ready`, das Betriebssystem wird in einem getrennten Schritt über die Oberfläche eingespielt. Der Befehl deckt damit nur einen Teil des Ablaufs ab.

Es findet keine Prüfung der Eingaben statt. Die Anzahl der gewünschten Maschinen wird ganzzahlig durch die Anzahl der Hosts geteilt. Bei sechs Hosts und der Anforderung von zehn Maschinen entstehen sechs. Diese Einschränkung ist in der Anleitung des Projekts ausdrücklich beschrieben, wird vom Skript aber nicht durchgesetzt: eine unzulässige Eingabe führt nicht zu einem Fehler, sondern ohne Meldung zu einem anderen Ergebnis als angefordert. Das Profil m254 gibt mit `count: 20` bei sechs Hosts selbst einen Wert vor, der dieser Einschränkung nicht entspricht.

Es gibt keine Rückmeldung über den Erfolg. Das Skript wartet nicht, prüft nichts nach und meldet keinen Zustand. Ob die Maschinen später nutzbar sind, zeigt sich erst in der Oberfläche.

Diese drei Punkte, fehlende Vollständigkeit, fehlende Validierung und fehlende Zustandsführung, sind die Ansatzpunkte des in Kapitel 4.3 beschriebenen Agenten.

#### 3.2.5 Ablauf und Zählung der manuellen Schritte

Die folgende Aufstellung ist nicht aus der Anleitung abgeleitet, sondern an einem vollständigen Durchlauf beobachtet. Dieser Lernlauf wurde am 16.09.2026 auf `cloud-au-30` in der Zone `10-1-45-0` durchgeführt, mit dem Profil m254 und einer Maschine. Er diente ausdrücklich der Ermittlung des Ablaufs und ist nicht Teil der Ausgangsmessung. Das Protokoll liegt als `docs/nachweise/lernlauf-lernmaas-00-20260916.txt` im Repository.

| Nr | Schritt | Art |
| --- | --- | --- |
| 1 | WireGuard-Verbindung zum Rack aufbauen | manuell |
| 2 | Per SSH auf den MAAS-Controller verbinden | manuell |
| 3 | `createvms` mit Profil und Anzahl aufrufen | manuell |
| 4 | Commissioning abwarten | automatisch |
| 5 | Zone in der Oberfläche setzen | manuell |
| 6 | Deploy-Dialog öffnen | manuell |
| 7 | Betriebssystem wählen | manuell |
| 8 | Erstkonfiguration in das Textfeld einfügen | manuell |
| 9 | Bereitstellung bestätigen | manuell |
| 10 | Bereitstellung abwarten | automatisch |
| 11 | Adresse der Maschine ermitteln | manuell |
| 12 | Testdienst prüfen | manuell |
| 13 | Maschine freigeben | manuell |
| 14 | Maschine löschen | manuell |
| 15 | Resource Pool löschen | manuell |

Damit ergeben sich dreizehn manuelle Schritte, davon fünf in einer grafischen Oberfläche, während zwei Schritte ohne Zutun ablaufen.

Zeitlicher Verlauf des beobachteten Laufs:

| Abschnitt | Von | Bis | Dauer | Art |
| --- | --- | --- | --- | --- |
| Aufruf von `createvms` | 13:05:19 | 13:05:40 | 21 s | manuell |
| Commissioning bis `Ready` | 13:05:35 | 13:08:12 | 157 s | automatisch |
| Bedienung in der Oberfläche | 13:08:12 | 13:09:05 | 53 s | manuell |
| Bereitstellung bis `Deployed` | 13:09:05 | 13:14:48 | 343 s | automatisch |
| **Aufbau gesamt** | 13:05:19 | 13:14:48 | 569 s | |
| Abbau gesamt | 13:19:30 | 13:20:46 | 76 s | überwiegend manuell |

Die Bearbeitungszeit einer Person betrug damit rund 74 Sekunden beim Aufbau und rund 40 Sekunden beim Abbau. Der weitaus grösste Teil der Gesamtdauer ist Wartezeit des Systems.

Drei Beobachtungen aus diesem Lauf waren in der Anleitung nicht beschrieben:

Das Commissioning läuft nach `createvms` selbsttätig an und dauerte 157 Sekunden. Der Zustand `Ready` wird also nicht unmittelbar erreicht, und die Bereitstellung kann erst danach ausgelöst werden.

Die Adresse der Maschine wechselt. Während des Commissionings lautete sie `10.0.45.250`, nach der Bereitstellung `10.0.45.56`. Eine automatisierte Prüfung darf die Adresse deshalb nicht annehmen, sondern muss sie aus der Plattform auslesen.

Die Erstkonfiguration wird bei jedem Lauf von Hand eingefügt. Der Bereitstellungsdialog enthält ein Textfeld für cloud-init. Dessen Inhalt ist nicht Teil des Modulprofils, wird nicht versioniert und nicht geprüft. Ein Tippfehler wird deshalb erst erkennbar, wenn die Maschine später nicht das erwartete Verhalten zeigt.

Der Lauf belegt zugleich, dass sich über dieses Textfeld derselbe prüfbare Dienst einrichten lässt wie auf der Zielplattform dieser Arbeit. Damit ist das in Kapitel 3.4.2 verlangte einheitliche Endkriterium auf beiden Seiten herstellbar. Die Prüfung ergab die erwartete Antwort des Testdienstes über Port 8080. Die Zeichenkette der Antwort wurde nach dem Lernlauf auf beiden Plattformen auf `lernumgebung bereit` vereinheitlicht, damit die Prüfung auf beiden Seiten mit demselben Befehl erfolgen kann.

#### 3.2.6 Abbau

Ein dem Aufbau entsprechender Abbaubefehl existiert nicht. Der Abbau wurde im selben Lauf beobachtet und besteht aus drei getrennten Vorgängen.

| Vorgang | Wirkung | Dauer |
| --- | --- | --- |
| Freigeben | Die Maschine wechselt zurück nach `Ready`. Sie bleibt bestehen | 5 s |
| Maschine löschen | Die Maschine verschwindet, die Ressourcen des Hosts werden freigegeben | 6 s |
| Resource Pool löschen | Der beim Aufbau angelegte Pool wird entfernt | eigener Vorgang |

Der wesentliche Befund lautet, dass das Freigeben keinen Abbau darstellt. Nach dem Freigeben war die Maschine weiterhin vorhanden, die Gesamtzahl unverändert bei 31, und der beim Aufbau angelegte Resource Pool `m254-da01` bestand weiter. Erst das Löschen der Maschine gab die Ressourcen des Virtualisierungshosts zurück, nachweisbar an den Werten von 10 auf 8 Kernen, von 10240 auf 8192 MB und von 60 auf 48 GB. Der Resource Pool blieb auch danach bestehen und musste getrennt entfernt werden.

Im heutigen Vorgehen wird nicht geprüft, ob nach einem Abbau Ressourcen zurückbleiben. Es gibt keinen Befehl, der den Endzustand feststellt, und keine Meldung, die Vollständigkeit bestätigt.

Eine weitere Beobachtung betrifft die Nachweisführung selbst: Die Ereignisabfrage von MAAS löst über den Hostnamen auf. Nach dem Löschen der Maschine lieferte sie keine Daten mehr. Nachweise müssen deshalb erhoben werden, solange die Objekte bestehen. Diese Regel wurde in die Messprotokollvorlage übernommen.

#### 3.2.7 Zusammenfassung der Befunde

| Nr | Befund | Beleg |
| --- | --- | --- |
| B1 | Eine deklarative Beschreibung existiert, ist aber an MAAS und KVM gebunden | `config.yaml`, Felder für `maas pod compose` |
| B2 | Die Beschreibung wird nicht gegen ein Schema geprüft | Textparser im Skript, keine Validierung |
| B3 | Eine dokumentierte Einschränkung wird nicht durchgesetzt | Ganzzahldivision in `createvms`, `count: 20` bei sechs Hosts |
| B4 | Der Befehl erzeugt keine nutzbare Umgebung, der Rest läuft in der Oberfläche | Zustand `Ready` nach dem Lauf, sechs Schritte in der Oberfläche |
| B5 | Es gibt keine Zustandsführung und keine Erfolgsmeldung | Skript wartet nicht und prüft nicht nach |
| B6 | Es gibt keinen definierten Abbau und keinen Nachweis der Vollständigkeit | kein Gegenstück zu `createvms` |
| B7 | Die Konfiguration liegt in fünf unabhängigen Kopien | gleiche Prüfsumme auf fünf Controllern, einzeln nachgezogen |
| B8 | Die Belegung wird ausserhalb des Systems von Hand geführt | Reservationsliste, Abweichung zur Zone `10-4-45-0` |
| B9 | Virtuelle Maschinen sind steuerbar, die Hosts darunter nicht | Stromsteuerung `Manual` auf den Bare-Metal-Maschinen |
| B10 | Zwischen Aufruf und Bereitstellung liegt ein automatischer Zwischenschritt von rund 157 Sekunden | Commissioning im Lernlauf vom 16.09.2026 |
| B11 | Die Adresse der Maschine steht erst nach der Bereitstellung fest | Wechsel von 10.0.45.250 auf 10.0.45.56 |
| B12 | Die Erstkonfiguration ist nicht Teil des Profils und wird von Hand eingefügt | Textfeld im Bereitstellungsdialog |
| B13 | Freigeben ist kein Abbau, der vollständige Abbau besteht aus drei Vorgängen | Kapitel 3.2.6 |
| B14 | Der Resource Pool bleibt nach dem Löschen der Maschine bestehen | Kapitel 3.2.6 |

Die Befunde B2, B3, B5, B6, B11, B12, B13 und B14 adressiert diese Arbeit unmittelbar. B1 und B7 werden im Ausblick aufgegriffen. B9 bleibt ausserhalb des Umfangs, weil er die Hardware betrifft, B10 ist eine Eigenschaft der Plattform und wird lediglich in der Messung berücksichtigt.

#### 3.2.8 Quellen und Umgang mit internen Unterlagen

| Quelle | Art | Verwendung |
| --- | --- | --- |
| `mc-b/lernmaas`, insbesondere `helper/README.md` und `config.yaml` | öffentlich, GitHub | Ablauf, Aufrufsyntax, Einschränkungen der Hilfsskripte |
| `mc-b/lerncloud` | öffentlich, GitHub | Dienste und Erstkonfiguration der Lernumgebungen |
| Kurzanleitung TBZ-Cloud, Marcel Bernet, V1.0 | intern | Aufbau der Netze und des WireGuard-Zugangs |
| Erhebung auf den fünf MAAS-Controllern am 14.09.2026 | eigene Aufnahme | Zustand, Profile, Prüfsummen, Zonenbelegung |
| Reservationsliste LernMAAS TBZ | intern | Belegung der VPN-Umgebungen |
| Betriebsunterlagen in Teams, SharePoint und dem internen GitLab | intern | Hintergrund zu Betrieb und Upgrade-Planung |

Für interne Unterlagen gilt in dieser Arbeit eine feste Regel: Sie werden benannt und mit Ablageort referenziert, aber nicht wiedergegeben. Weder Bildschirmfotos ihrer Inhalte noch kopierte Adress- oder Schlüsseltabellen sind Teil dieser Dokumentation. Grund ist, dass das Repository dieser Arbeit öffentlich ist. Aussagen aus internen Quellen werden in eigenen Worten formuliert und, wo möglich, durch eine eigene Erhebung belegt.

### 3.3 Ableitung der Test-Lernumgebung

Der Proof of Concept verwendet eine einzige, technisch reduzierte Lernumgebung. Sie muss zwei Bedingungen erfüllen: sie muss sich nachvollziehbar aus den bestehenden Modulprofilen ableiten, und sie muss auf beiden Zielplattformen gleichwertig herstellbar sein.

#### 3.3.1 Übernommene Merkmale

| Merkmal | Wert | Begründung |
| --- | --- | --- |
| Anzahl Maschinen | 1 | Der vollständige Lebenszyklus lässt sich an einer Maschine prüfen. Die Anzahl ist ein Vervielfältiger, kein zusätzlicher Erkenntnisgewinn |
| Kerne | 2 | Alle drei Profile verwenden zwei Kerne |
| Arbeitsspeicher | 2048 MB | Wert von m239 und m254. Der höhere Wert von m426 ist auf Docker und Kubernetes zurückzuführen, die nicht übernommen werden |
| Datenträger | 12 GB | Wert von m254, zugleich der Wert der im Betrieb vorgefundenen Lern-Maschinen |
| Betriebssystem | Ubuntu 24.04 LTS | Auf den bereitgestellten Lern-Maschinen vorgefunden |
| Zugang | SSH mit hinterlegtem öffentlichem Schlüssel | Entspricht `services.ssh: generate`, ohne die heutige Passworterzeugung |
| Prüfbarer Dienst | ein Dienst über einen festgelegten Port | Ersetzt die profilabhängigen Dienste durch ein einziges, maschinell prüfbares Merkmal |

#### 3.3.2 Bewusst nicht übernommene Merkmale

| Merkmal | Begründung des Ausschlusses |
| --- | --- |
| `services.nfs`, `samba` | Binden die Umgebung an die örtliche Infrastruktur und sind in der Public Cloud nicht gleichwertig herstellbar |
| `services.docker`, `k8s` | Verlängern die Bereitstellung erheblich und unterscheiden sich je Profil. Für den Nachweis des Lebenszyklus ohne Bedeutung |
| `services.wireguard` | Der Zugang über das Labor-VPN ist plattformgebunden. An seine Stelle tritt die Erreichbarkeit des Dienstes über einen festgelegten Port |
| `services.firewall` | In allen drei Profilen ausgeschaltet |
| `repositories` | Die Modulinhalte sind für die technische Machbarkeit ohne Bedeutung |
| `vm.count` | Wird in der Test-Lernumgebung auf eins gesetzt, siehe oben |

#### 3.3.3 Festlegung

| Feld | Wert |
| --- | --- |
| Anzahl Maschinen | 1 |
| Rolle | Server |
| Betriebssystem | ubuntu-24.04 |
| Kerne | 2 |
| Arbeitsspeicher | 2048 MB |
| Datenträger | 12 GB |
| Zugang | SSH, öffentlicher Schlüssel |
| Prüfbarer Dienst | HTTP auf Port 8080, Antwort mit der Zeichenkette `lernumgebung bereit` |
| Endzustand | Die Umgebung gilt als bereit, wenn der Dienst diese Zeichenkette liefert |

Diese Festlegung deckt sich weitgehend mit der in Kapitel 4.1 aufgebauten Referenz-Lernumgebung, die mit zwei Kernen, 2 GB und 10 GB betrieben wurde. Der Datenträger wird von 10 auf 12 GB angehoben, damit er dem im Betrieb vorgefundenen Wert entspricht.

Die Spezifikation ist mit dem Firmenexperten abzustimmen.

### 3.4 Messkonzept

Das Messkonzept legt fest, was verglichen wird, wie gemessen wird und welche Aussagen die Messwerte tragen. Es wird vor der Ausgangsmessung festgeschrieben, damit die Messgrössen nicht nachträglich zum Ergebnis passend gewählt werden können.

#### 3.4.1 Grundsatz des Vergleichs

Verglichen wird das Verfahren, nicht die Hardware. Diese Unterscheidung ist notwendig, weil die beiden Vorgehensweisen nachweislich auf unterschiedlichen Systemen laufen: das heutige Vorgehen auf den älteren HP-Rechnern der LernMAAS-Umgebung, der Proof of Concept auf `dl380-01`. Ein direkter Vergleich roher Laufzeiten wäre damit nicht aussagekräftig.

Die Messgrössen sind deshalb so gewählt, dass die Hauptaussage von der eingesetzten Hardware unabhängig ist.

| Rang | Messgrösse | Hardwareabhängig | Begründung |
| --- | --- | --- | --- |
| 1 | Anzahl manueller Schritte einer Person, von der Anforderung bis zur nutzbaren Lernumgebung | Nein | Ein Schritt bleibt ein Schritt, unabhängig davon, wie schnell die Maschine rechnet. Das ist die zentrale Aussage der Arbeit |
| 2 | Bearbeitungszeit der Person, also die Zeit, in der jemand tatsächlich etwas tut | Gering | Wird durch die Hardware nur geringfügig beeinflusst |
| 3 | Reproduzierbarkeit, gemessen als Anzahl Durchläufe ohne manuelle Korrektur | Nein | Prüft, ob das Verfahren verlässlich ist |
| 4 | Vollständigkeit des Abbaus | Nein | Prüft, ob nach dem Abbau Reste zurückbleiben |
| 5 | Wartezeit des Systems, also die Zeit, in der die Person nichts tut | Ja | Wird ausgewiesen, aber nicht als Beleg für den Nutzen verwendet |

Die Gesamtdauer ergibt sich aus Bearbeitungszeit und Wartezeit und wird ebenfalls protokolliert. Sie wird jedoch immer zusammen mit dem Hinweis auf die unterschiedliche Hardware ausgewiesen. Damit bleibt die Aussage der Arbeit belastbar, auch wenn die neue Plattform die stärkere Maschine ist.

#### 3.4.2 Identische Start- und Endkriterien

Beide Vorgehensweisen werden am selben Punkt gestartet und am selben Punkt als fertig betrachtet.

| | Kriterium |
| --- | --- |
| **Start** | Die Anforderung einer Lernumgebung liegt vor, die Zielumgebung ist leer, keine Vorarbeit ist geleistet |
| **Ende Aufbau** | Der Testdienst liefert über das Netz auf Port 8080 die Zeichenkette `lernumgebung bereit`. Nicht: die Maschine läuft, nicht: der Befehl ist abgesetzt |
| **Ende Abbau** | Keine dem Lauf zugeordnete Ressource ist mehr vorhanden, einschliesslich des PersistentVolume. Nicht: der Löschbefehl ist abgesetzt |

Das Endkriterium des Abbaus ist bewusst so streng formuliert. Der Referenzlauf in Kapitel 4.1.3 hat gezeigt, dass zwischen dem abgesetzten Befehl und dem tatsächlichen Verschwinden aller Ressourcen Zeit vergeht. Eine Messung, die nur den abgesetzten Befehl erfasst, bildet diesen Zeitraum nicht ab.

#### 3.4.3 Umgang mit dem Abbildimport

Der Referenzlauf hat gezeigt, dass der Import des Betriebssystemabbilds den grössten Teil der Gesamtdauer ausmacht. Wird dieser Anteil ungleich behandelt, misst der Vergleich vor allem die Internetanbindung der jeweiligen Umgebung.

Regel: Das Betriebssystemabbild liegt bei beiden Vorgehensweisen zu Beginn der Messung lokal vor. Der Import aus dem Internet wird einmalig vorbereitet und ist nicht Teil der Messung. Ist das auf einer der beiden Seiten technisch nicht möglich, wird der Importanteil getrennt ausgewiesen und aus dem Vergleich herausgerechnet, und dieser Umstand wird im Messprotokoll vermerkt.

#### 3.4.4 Durchführung

- Je Vorgehensweise werden drei vollständige Durchläufe protokolliert, Aufbau und Abbau.
- Gemessen wird mit derselben Test-Lernumgebung nach Kapitel 3.3.
- Die Zeitnahme erfolgt mit Zeitstempeln, nicht durch Schätzung. Jeder Schritt wird mit Beginn und Ende erfasst.
- Manuelle Schritte werden einzeln aufgeführt, nicht nur gezählt. Nur so ist nachvollziehbar, welche Schritte durch die neue Lösung tatsächlich entfallen.
- Auch vorbereitende manuelle Schritte zählen, etwa die Reservation einer VPN-Umgebung oder das Eintragen in eine Liste.

#### 3.4.5 Messprotokollvorlage

Die Vorlage liegt als `docs/messungen/vorlage-messprotokoll.md` im Repository und enthält je Durchlauf:

| Feld | Inhalt |
| --- | --- |
| Kennung des Laufs | eindeutig, etwa `lernmaas-01` oder `poc-kubevirt-02` |
| Vorgehensweise | heutiges Vorgehen oder Proof of Concept |
| Umgebung | System, Netz, Hardware |
| Datum und ausführende Person | |
| Schrittliste | je Schritt: Beschreibung, Beginn, Ende, manuell oder automatisch |
| Bearbeitungszeit, Wartezeit, Gesamtdauer | in Sekunden |
| Anzahl manueller Schritte | |
| Manuelle Korrekturen | Anzahl und Beschreibung |
| Abbau | Endzustand, Zeitpunkt des Verschwindens der letzten Ressource |
| Bemerkungen und Auffälligkeiten | |

#### 3.4.6 Erklärte Einschränkungen

Diese Einschränkungen werden offen ausgewiesen und bei der Bewertung in Kapitel 6 berücksichtigt:

1. **Unterschiedliche Hardware.** Die beiden Vorgehensweisen laufen nicht auf denselben Maschinen. Deshalb ist die Anzahl manueller Schritte und nicht die Gesamtdauer die tragende Messgrösse.
2. **Kleine Stichprobe.** Drei Durchläufe je Vorgehensweise erlauben keine statistische Auswertung. Sie genügen, um einen Unterschied in der Grössenordnung zu belegen, nicht um kleine Unterschiede nachzuweisen.
3. **Dieselbe ausführende Person.** Alle Durchläufe werden von derselben Person ausgeführt, die das heutige Verfahren kennt. Ein Einarbeitungseffekt zugunsten der neuen Lösung ist damit weitgehend ausgeschlossen, ein Routineeffekt zugunsten des heutigen Verfahrens besteht dagegen.
4. **Reduzierte Test-Lernumgebung.** Gemessen wird nicht eine vollständige Unterrichtsumgebung, sondern die reduzierte Umgebung nach Kapitel 3.3.

### 3.5 Ausgangsaufnahme des heutigen Verfahrens

#### 3.5.1 Gegenstand und Abgrenzung

Dieser Abschnitt hält fest, wie sich das heutige Verfahren im Betrieb tatsächlich verhält. Er ist bewusst nicht als Vorher-Nachher-Vergleich angelegt. Ein solcher Vergleich setzt voraus, dass beide Seiten in ihrer vorgesehenen Form vorliegen, und die neue Seite entsteht erst in Sprint 2. Der Vergleich erfolgt deshalb in Kapitel 6, auf Grundlage der Durchläufe aus US28 und US30.

Was hier erhoben wird:

| Erhoben | Nicht erhoben |
| --- | --- |
| Anzahl und Art der manuellen Schritte je Lernumgebung | Ein Zeitvergleich zwischen altem und neuem Verfahren |
| Verhalten des Verfahrens im Fehlerfall | Werte für eine Lernumgebung in Klassengrösse |
| Zeitanteile innerhalb des heutigen Verfahrens | Aussagen über die Leistungsfähigkeit der Hardware |

Die Läufe wurden am 16.09.2026 in der Zone `10-1-45-0` auf `cloud-au-30` durchgeführt, mit dem Profil m254 und je einer Maschine. Die Protokolle liegen unter `docs/messungen/`.

#### 3.5.2 Durchgeführte Läufe

| Kennung | Zweck | Ergebnis |
| --- | --- | --- |
| `lernmaas-00` | Lernlauf zur Ermittlung des Ablaufs | vollständig, Aufbau 569 s, Abbau 76 s |
| `mess01` | Aufnahme mit vollständigem Protokoll | vollständig, Aufbau 673 s |
| `parallel01` | Versuch mit zwei Maschinen gleichzeitig | abgebrochen, eine von zwei Maschinen entstanden |

#### 3.5.3 Manuelle Schritte je Lernumgebung

Das wesentliche Ergebnis dieser Aufnahme ist nicht eine Zeitangabe, sondern eine Anzahl. Der Grund steht in Kapitel 3.4.1: die Anzahl der manuellen Schritte ist die einzige Messgrösse, die von der eingesetzten Hardware unabhängig ist.

Massgeblich ist dabei die Bezugsgrösse. Die dreizehn manuellen Schritte aus Kapitel 3.2.5 fallen je Lernumgebung an, nicht je virtueller Maschine. Ob eine Umgebung aus einer oder aus vierundzwanzig Maschinen besteht, ändert daran nichts: `createvms` wird einmal aufgerufen, die Maschinen werden gemeinsam einer Zone zugeordnet, gemeinsam markiert und gemeinsam bereitgestellt, die Erstkonfiguration wird einmal eingefügt.

Daraus folgt eine Einordnung, die für die Bewertung in Kapitel 6 wesentlich ist: Der Aufwand des heutigen Verfahrens ist ein fixer Aufwand je Umgebung. Der Nutzen einer Automatisierung liegt deshalb nicht darin, Arbeit pro Maschine zu sparen, sondern darin, diesen fixen Block zu ersetzen und die darin enthaltenen fehleranfälligen Handgriffe zu beseitigen.

#### 3.5.4 Zeitanteile innerhalb des heutigen Verfahrens

Die folgenden Werte beschreiben den Ablauf für eine Maschine. Sie sind nicht mit Werten einer anderen Plattform vergleichbar, weil die Hardware unterschiedlich ist und weil die Grösse der Umgebung die automatischen Anteile beeinflusst.

| Abschnitt | `lernmaas-00` | `mess01` | Art |
| --- | --- | --- | --- |
| Aufruf von `createvms` | 21 s | 20 s | manuell |
| Commissioning bis `Ready` | 157 s | 155 s | automatisch |
| Von `Ready` bis `Deploying` | 53 s | 178 s | Liegezeit und Bedienung |
| Bereitstellung bis `Deployed` | 343 s | 326 s | automatisch |
| **Aufbau gesamt** | 569 s | 673 s | |

Die automatischen Abschnitte sind über beide Läufe stabil, die Abweichung liegt unter vier Prozent. Die Spanne zwischen `Ready` und `Deploying` schwankt dagegen stark, weil sie zwei verschiedene Dinge enthält: die Zeit, bis die bedienende Person überhaupt bemerkt, dass die Maschine bereit ist, und die eigentliche Bedienung. Die bedienende Person schätzt den Bedienanteil auf 60 bis 90 Sekunden. Für künftige Läufe wird der Beginn der Bedienung als eigener Zeitstempel erfasst, damit beide Anteile getrennt ausgewiesen werden können.

Der Abbau dauerte in beiden Läufen unter zwei Minuten und besteht aus drei getrennten Vorgängen, siehe Kapitel 3.2.6.

#### 3.5.5 Verhalten im Fehlerfall

Der Lauf `parallel01` sollte zwei Maschinen gleichzeitig anlegen. Die erste entstand auf `cloud-au-32`, die zweite scheiterte auf `cloud-au-36`:

```text
maas ubuntu pod compose 9 memory=2048 cores=2 storage=12 pool=15 hostname=m254-02-parallel01
Unable to compose machine because: Failed talking to pod: Virsh command
['vol-create-as', 'maas', 'd2e935e2-...', '12000000000', ...] failed
error: Failed to create file '/var/lib/libvirt/maas-images/d2e935e2-...':
Input/output error
```

Die Ursache liegt ausserhalb dieser Arbeit: `cloud-au-36` meldet in MAAS einen Datenträgerfehler. Der Befund wurde dem Betreiber gemeldet.

Für diese Arbeit ist weniger die Ursache von Bedeutung als das beobachtete Verhalten des Verfahrens:

| Beobachtung | Folge |
| --- | --- |
| Der Resource Pool war bereits angelegt und blieb bestehen | Eine verbleibende Ressource ohne automatische Bereinigung |
| Die erste Maschine blieb bestehen und lief weiter | Eine unvollständig aufgebaute Umgebung |
| Es wurde kein anderer Host versucht | Fünf freie Hosts blieben ungenutzt |
| Es gab keine zusammenfassende Meldung | Der Fehler steht mitten in der Ausgabe |
| Es gab keine Prüfung, ob das Ergebnis der Anforderung entspricht | Bestellt waren zwei Maschinen, entstanden ist eine |

Der letzte Punkt hat die grösste Tragweite. Ohne Prüfung der Ausgabe ist nicht erkennbar, dass weniger Maschinen entstanden sind als angefordert. Bei zwei angeforderten Maschinen ist eine fehlende Maschine noch erkennbar, bei einer Klasse mit vierundzwanzig Maschinen kann die Abweichung dagegen unbemerkt bleiben, bis die Umgebung im Unterricht benötigt wird.

Damit ist an einem tatsächlichen Vorfall belegt, was die Befunde B3, B5 und B6 aus Kapitel 3.2.7 beschreiben: es fehlt eine Prüfung der Eingabe, eine Zustandsführung und eine verlässliche Rückmeldung. Diese drei Eigenschaften sind Gegenstand des Agenten in Kapitel 4.3.

#### 3.5.6 Was diese Aufnahme nicht leistet

1. **Kein Zeitvergleich.** Die Gegenseite existiert noch nicht. Der Vergleich erfolgt in Kapitel 6.
2. **Keine Klassengrösse.** Gemessen wurde mit einer Maschine. Dass der manuelle Aufwand bei grösseren Umgebungen gleich bleibt, ist aus dem Ablauf begründet, aber noch nicht an einem Lauf belegt. Ein einzelner Lauf in Klassengrösse ist dafür vorgesehen und mit dem Betreiber abzustimmen.
3. **Keine Stichprobe.** Zwei vollständige Läufe erlauben keine Aussage über Streuung.

Diese Einschränkungen werden in Kapitel 6 erneut aufgegriffen.

### 3.6 Auswahl der Public-Cloud-Plattform

> Wird in Sprint 1 erarbeitet, User Stories US14 und US15. Inhalt: Nutzwertanalyse mit vorab gewichteten Kriterien, Entscheid als ADR-004, Ergebnis des Smoke-Tests inklusive Kostenkontrolle.

### 3.7 Zielarchitektur

> Wird in Sprint 1 erarbeitet, User Story US16. Inhalt: Systemkontext, Komponentensicht, Trennung zwischen Fachmodell, Agent und Adaptern.
## 4 Umsetzung

### 4.1 Referenz-Lernumgebung auf KubeVirt

Bevor ein Fachmodell entworfen werden kann, muss feststehen, welche Felder eine Lernumgebung auf der Zielplattform überhaupt benötigt. Diese Felder wurden nicht aus der Dokumentation von KubeVirt abgeleitet, sondern aus einer von Hand aufgebauten, lauffähigen Referenz-Lernumgebung. Der Lauf dient drei Zwecken: er belegt die Machbarkeit auf der gewählten Plattform, er liefert die Ausgangsgrössen für die spätere Messung, und er ist die Quelle für die Feldtrennung, auf der das Fachmodell in Kapitel 4.2 aufbaut.

Der Lauf trägt die Kennung `testlauf-01` und wurde am 14.09.2026 auf `dl380-01` durchgeführt. Das vollständige Manifest liegt als `docs/nachweise/testvm.yaml` im Repository, die Konsolenausgaben unter `docs/nachweise/`.

#### 4.1.1 Aufbau der Referenzumgebung

Die Umgebung besteht aus vier Bausteinen, die zusammen in einer einzigen Manifestdatei beschrieben sind.

| Baustein | Zweck |
| --- | --- |
| Namensraum `diplomarbeit` | Klammert alle Objekte eines Laufs und erlaubt später den Abbau über eine einzige Grenze |
| `DataVolume` als Vorlage in der VM | Lädt das Ubuntu-Abbild herunter und legt daraus den Datenträger der Maschine an |
| `VirtualMachine` | Beschreibt die Maschine selbst: Kerne, Arbeitsspeicher, Datenträger, Netzwerk, Erstkonfiguration |
| `Service` vom Typ NodePort | Macht den Testdienst in der Maschine von aussen prüfbar, siehe ADR-002 |

Die wesentlichen Teile des Manifests im Überblick, gekürzt um die Abschnitte `volumes` und `Service`, die vollständige Datei liegt als `docs/nachweise/testvm.yaml` im Repository:

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: testvm
  namespace: diplomarbeit
  labels:
    lauf: testlauf-01
spec:
  runStrategy: Always
  dataVolumeTemplates:
    - metadata:
        name: testvm-disk
      spec:
        storage:
          resources:
            requests:
              storage: 10Gi
          storageClassName: microk8s-hostpath
          accessModes:
            - ReadWriteOnce
        source:
          http:
            url: https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
  template:
    metadata:
      labels:
        kubevirt.io/domain: testvm
        app: testvm
        lauf: testlauf-01
    spec:
      domain:
        cpu:
          cores: 2
        memory:
          guest: 2Gi
        devices:
          disks:
            - name: rootdisk
              disk:
                bus: virtio
            - name: cloudinit
              disk:
                bus: virtio
          interfaces:
            - name: default
              masquerade: {}
      networks:
        - name: default
          pod: {}
```

Drei Punkte daran sind für das weitere Vorgehen wichtig.

Die Erstkonfiguration erfolgt über cloud-init. Die Maschine erhält beim ersten Start ein Benutzerkonto mit hinterlegtem öffentlichem Schlüssel und legt einen Dienst `testdienst.service` an, der einen einfachen Webserver auf Port 8080 betreibt. Damit gibt es einen eindeutigen, maschinell prüfbaren Endzustand: die Lernumgebung gilt erst dann als bereit, wenn dieser Dienst antwortet. Ohne einen solchen Endzustand liesse sich nicht eindeutig bestimmen, zu welchem Zeitpunkt eine Messung endet.

Das Netzwerk läuft über `masquerade` am Pod-Netz. Die Maschine erhält keine Adresse im Labornetz, sondern erscheint nach aussen unter der Adresse ihres Pods. Zusammen mit dem NodePort-Service ist der Testdienst damit aus dem Verwaltungsnetz unter `10.1.24.5:30080` erreichbar, ohne dass am Netzwerk des Hosts etwas geändert werden muss. Damit ist ADR-002 praktisch umgesetzt, und der bestehende Fernzugriff auf den Host bleibt unverändert.

Alle Objekte eines Laufs tragen das Label `lauf: testlauf-01`. Dieses Label ist die spätere Grundlage für den vollständigen Abbau und für die Zuordnung von Objekten zu einem Lauf, weshalb es in das Fachmodell übernommen wird.

#### 4.1.2 Ablauf und Messwerte des Referenzlaufs

Der Lauf wurde mit einem einzigen `apply` gestartet und anschliessend beobachtet, bis der Testdienst antwortete.

| Grösse | Wert |
| --- | --- |
| Zeit von `apply` bis antwortender Testdienst | 324 Sekunden |
| Davon Abbildimport durch CDI | überwiegender Anteil |
| Manuelle Schritte während des Laufs | keine, nach dem Absetzen des Befehls |
| Zustandsfolge `DataVolume` | `Pending`, `ImportScheduled`, `ImportInProgress`, `Succeeded` |
| Zustandsfolge `VirtualMachineInstance` | `Scheduling`, `Scheduled`, `Running` |
| Prüfung des Endzustands | HTTP-Antwort des Testdienstes über NodePort |

Die 324 Sekunden sind kein Vergleichswert, da der Lauf ein Machbarkeitsnachweis mit einem von Hand geschriebenen Manifest war und nicht der Ablauf, den die fertige Lösung nehmen wird. Er wird deshalb in keinem Vergleich mit dem heutigen Verfahren verwendet. Festzuhalten ist lediglich, dass der Abbildimport den grössten Teil dieser Zeit ausmacht. Das Messkonzept muss deshalb festlegen, ob der Import bei jedem Durchlauf neu erfolgt oder ob ein zwischengespeichertes Abbild verwendet wird. Beide Vorgehensweisen sind vertretbar, sie müssen nur bei beiden verglichenen Verfahren gleich gehandhabt werden, da der Vergleich sonst nicht aussagekräftig ist.

Die beobachtete Zustandsfolge ist zugleich der erste Entwurf der Zustandsführung des Agenten. Der Agent muss den Bereitschaftszustand einer Umgebung nicht abschätzen, sondern kann denselben Zustandsübergängen folgen, die die Plattform ohnehin meldet, und erst am Ende den fachlichen Readiness-Check durchführen.

#### 4.1.3 Abbau und ein Befund mit Folgen für den Entwurf

Nach dem Lauf wurde die Umgebung abgebaut. Der Abbau war vollständig, erfolgte aber verzögert: unmittelbar nach dem Löschen zeigte das zugehörige PersistentVolume noch den Zustand `Released`, erst bei einer späteren Prüfung war es verschwunden.

Der Befund hat keine Auswirkung auf den Lauf selbst, wirkt sich aber unmittelbar auf den Entwurf des Agenten aus:

- Ein Abbau darf nicht bereits dann als erfolgreich gemeldet werden, wenn der Löschbefehl abgesetzt ist, da zu diesem Zeitpunkt noch Objekte vorhanden sein können.
- Der Agent muss auf den tatsächlichen Endzustand warten, also auf das Verschwinden aller Objekte des Laufs, und dieses Warten muss mit einer Zeitgrenze versehen sein.
- Läuft die Zeitgrenze ab, ist das Ergebnis ein klar benannter Fehlerzustand mit Angabe der verbliebenen Objekte und keine Erfolgsmeldung.

Diese Anforderung ist in die User Stories US20, Abbau über den Agenten, und US29, Nachweis des vollständigen Abbaus, eingeflossen und dort als Akzeptanzkriterium festgehalten. Der Befund ist damit ein Beispiel dafür, wie eine Erhebung im ersten Sprint eine Entwurfsentscheidung im zweiten Sprint bestimmt.

Ein zweiter Punkt betrifft die Prüfung selbst: Der Nachweis des vollständigen Abbaus wird über das Label `lauf` geführt. Abgefragt werden nicht einzelne Objektarten, sondern alle Objekte mit diesem Label im Namensraum. Nur so lassen sich auch Objekte erfassen, die von der Plattform selbst abgeleitet wurden, etwa das `DataVolume` aus der Vorlage.

#### 4.1.4 Trennung zwischen fachlicher und technischer Beschreibung

Die Trennung der Felder ist das wichtigste Ergebnis des Referenzlaufs. Die Felder des Manifests wurden danach geordnet, ob eine Lehrperson sie sinnvoll angeben kann oder ob sie sich aus der Zielplattform ergeben. Diese Trennung ist die Grundlage des plattformneutralen Fachmodells in Kapitel 4.2 und wird dort in ein JSON-Schema überführt.

| Feld im Manifest | Einstufung | Begründung |
| --- | --- | --- |
| Name der Lernumgebung, Kennung des Laufs | **Fachlich** | Bezeichnet, worum es geht. Muss von der Lehrperson kommen |
| Anzahl Maschinen und deren Rollen | **Fachlich** | Ergibt sich aus dem Modulprofil |
| Anzahl Kerne, Arbeitsspeicher, Grösse des Speichers | **Fachlich** | Fachliche Anforderung an die Leistung, plattformunabhängig ausdrückbar |
| Betriebssystem in der Form `ubuntu-24.04` | **Fachlich** | Fachliche Angabe. Die Zuordnung zur konkreten Abbild-URL ist Sache des Adapters |
| Benötigte Dienste und deren Ports | **Fachlich** | Bestimmt, wann die Umgebung fachlich bereit ist |
| Öffentliche Schlüssel der Zugangsberechtigten | **Fachlich** | Wer Zugriff erhält, ist eine fachliche Festlegung |
| `apiVersion`, `kind` | Technisch | Reine Plattformsyntax |
| `dataVolumeTemplates`, `source.http.url` | Technisch | Abbildbezug der Plattform. Wird vom Adapter aus dem fachlichen Betriebssystem abgeleitet |
| `storageClassName: microk8s-hostpath` | Technisch | Ergebnis von ADR-003, plattformspezifisch |
| `interfaces.masquerade`, `networks.pod` | Technisch | Netzwerkmodell der Plattform |
| `Service` vom Typ NodePort, Portnummer | Technisch | Ergebnis von ADR-002. Fachlich ist nur, dass der Dienst erreichbar sein muss |
| `cloudInitNoCloud`, Inhalt der Erstkonfiguration | Technisch, aus fachlichen Angaben erzeugt | Die Lehrperson gibt Dienste und Schlüssel an, der Adapter erzeugt daraus die Erstkonfiguration |
| `runStrategy`, Bus-Typen der Datenträger | Technisch | Betriebsdetails der Plattform |

Die Grenze verläuft also zwischen der Frage, was gebraucht wird, und der Frage, wie die jeweilige Plattform es herstellt. Diese Grenze begründet die Adapterschicht: dasselbe fachliche Dokument muss sowohl auf KubeVirt als auch in der Public Cloud zu einer gleichwertigen Umgebung führen. Sobald ein plattformspezifisches Feld in das Fachmodell wandert, ist diese Gleichwertigkeit nicht mehr gegeben.

Aus der Tabelle ergibt sich unmittelbar der erste Entwurf des Fachmodells:

```yaml
lernumgebung:
  name: m239-testlauf
  lauf: testlauf-01
  maschinen:
    - rolle: server
      anzahl: 1
      betriebssystem: ubuntu-24.04
      kerne: 2
      arbeitsspeicher: 2Gi
      speicher: 10Gi
      dienste:
        - name: testdienst
          port: 8080
      zugang:
        ssh:
          - ssh-rsa AAAA...
```

Dieses Dokument enthält kein Feld, das nur auf KubeVirt zutrifft. Es ist der Ausgangspunkt für US17 und wird dort formal als JSON-Schema festgelegt und validiert.

#### 4.1.5 Einordnung

| Aussage | Beleg |
| --- | --- |
| KubeVirt auf `dl380-01` kann eine vollständige Lernumgebung aus einem Manifest erzeugen | `testlauf-01`, 324 Sekunden bis zum antwortenden Dienst |
| Der Endzustand ist maschinell prüfbar | HTTP-Antwort über NodePort, Grundlage des Readiness-Checks |
| Der Abbau ist vollständig, aber nicht sofort | Befund zum PersistentVolume, Anforderung an US20 und US29 |
| Fachliche und technische Felder lassen sich sauber trennen | Tabelle in 4.1.4 |

Damit ist die technische Machbarkeit auf der On-Prem-Seite belegt und der Entwurf des Fachmodells sachlich begründet. Offen bleibt die Gegenseite in der Public Cloud, die in Kapitel 3.6 ausgewählt und in Kapitel 4.6 umgesetzt wird.

### 4.2 Plattformneutrales Fachmodell

> Wird in Sprint 1 und 2 erarbeitet, User Stories US17 und US18. Inhalt: JSON-Schema, Feldbeschreibungen, Validierung mit gültigen und ungültigen Beispieldokumenten.

### 4.3 Agent mit Zustandsführung

> Wird in Sprint 2 erarbeitet, User Stories US19 bis US21. Inhalt: Zustandsmodell, Aufbau, Readiness-Check, Abbau mit Wartelogik und Zeitgrenze, Fehlerbehandlung.

### 4.4 MCP-Schnittstelle

> Wird in Sprint 2 erarbeitet, User Stories US22 und US23. Inhalt: Werkzeugbeschreibungen, Trennung zwischen Agent und Adaptern, Fake-Adapter für die automatisierten Tests.

### 4.5 Adapter für KubeVirt

> Wird in Sprint 2 erarbeitet, User Story US24. Inhalt: Abbildung des Fachmodells auf die in 4.1.4 als technisch eingestuften Felder.

### 4.6 Adapter für die Public Cloud

> Wird in Sprint 2 und 3 erarbeitet, User Stories US25 und US26. Inhalt: Abbildung desselben Fachmodells auf die in Kapitel 3.6 gewählte Plattform, Kostenkontrolle, Abbau.

### 4.7 Protokollierung und Nachvollziehbarkeit

> Wird in Sprint 2 erarbeitet, User Story US27.

## 5 Tests und Messungen

> Wird in Sprint 3 erarbeitet. Enthält: Testkonzept mit positiven und negativen Anwendungsfällen, Readiness-Check, Protokolle der sechs vollständigen Durchläufe, Nachweis des vollständigen Abbaus, Messwerte.

## 6 Bewertung und Vergleich

> Wird in Sprint 3 erarbeitet. Enthält: Vorher-Nachher-Vergleich mit identischen Start- und Endkriterien, Nutzwertanalyse MCP-Adapter gegen direkte API-Anbindung, SWOT-Analyse, Wirtschaftlichkeitsbetrachtung, Beurteilung der Übertragbarkeit auf einen produktiven Betrieb.

## 7 Betrieb und Schulung

> Wird in Sprint 3 erarbeitet. Enthält: Runbook für Aufbau, Bedienung, Fehleranalyse und vollständigen Abbau, Schulungsunterlage und Einführung für Dozierende.

## 8 Projektverlauf

> Folgt in Stufe 4 und wächst über die Sprints. Enthält: Sprintplanungen, Sprint Reviews mit Expertenrückmeldungen, Retrospektiven, Verlauf der Risikobewertung. Verlinkt auf die wöchentlichen Statusberichte und das Projektjournal.

## 9 Reflexion

> Wird am Projektende verfasst. Gliederung: fachliche Reflexion, methodische Reflexion zur Projektführung mit Bezug auf Kapitel 2, persönliche Reflexion, Lessons Learned.

## 10 Fazit und Ausblick

> Wird am Projektende verfasst. Enthält: Zielerreichung im Detail gegen die Tabelle aus Kapitel 1.4, Gesamtfazit, Ausblick auf mögliche Weiterentwicklungen.

---

## Verzeichnisse

### Glossar

| Begriff | Bedeutung |
| --- | --- |
| KubeVirt | Erweiterung für Kubernetes, die den Betrieb virtueller Maschinen als Kubernetes-Ressourcen ermöglicht |
| MCP | Model Context Protocol, hier als einheitliches Kommunikationsprotokoll zwischen Agent und plattformspezifischen Adaptern eingesetzt |
| MAAS | Metal as a Service, Grundlage der heutigen Bereitstellung von Lernumgebungen an der TBZ |
| LernMAAS | Die TBZ-eigene Umsetzung der Lernumgebungen auf Basis von MAAS |
| Readiness-Check | Automatisierte Prüfung, ob die virtuelle Maschine läuft und der festgelegte Testdienst erreichbar ist |
| Teardown | Vollständiges Entfernen aller einem Testlauf zugeordneten Ressourcen |
| Story Point | Relative Schätzgrösse für Aufwand, Komplexität und Unsicherheit einer User Story |
| Velocity | Anzahl der in einem Sprint tatsächlich abgeschlossenen Story Points |

### Quellenverzeichnis

Texte und andere Teile dieser Arbeit, die nicht selbst verfasst wurden, sind an der betroffenen Stelle gekennzeichnet und mit einer Quellenangabe versehen.

| Nr. | Quelle | Abrufdatum |
| --- | --- | --- |
| Q1 | TBZ Höhere Fachschule, Merkblatt A Diplomprüfung, Stand Juni 2026 | 13.09.2026 |
| Q2 | Bewilligte Projektbeschreibung Diplomarbeit, Efekan Demirci, 10.09.2026 | 13.09.2026 |

### Abbildungsverzeichnis

| Nr. | Abbildung | Kapitel |
| --- | --- | --- |
| | | |

---

## Ehrenwort

> Wird unterschrieben dem Management Summary beigelegt.

## Kontakt

Efekan Demirci, ITCNE24, TBZ Höhere Fachschule
efekan.demirci@tbz.ch
