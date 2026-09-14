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

Die fachliche Beschreibung einer Lernumgebung und ihre technische Bereitstellung sind dabei eng mit dieser Plattform verbunden. Für eine andere Infrastruktur müssten Abläufe, Schnittstellen und Skripte separat angepasst oder neu entwickelt werden. Daraus entstehen zusätzlicher manueller Aufwand, eine stärkere Abhängigkeit von spezifischem Wissen einzelner Personen und eine eingeschränkte Wiederverwendbarkeit.

> Die detaillierte IST-Analyse folgt aus Sprint 1, User Story US07. Sie ergänzt diesen Abschnitt um den konkreten Ablauf, die beteiligten Komponenten und die manuellen Schritte des heutigen Vorgehens.

### 1.2 Problemstellung

Es fehlt ein einheitliches Modell, mit dem eine Lernumgebung unabhängig von der gewählten Plattform beschrieben und über einen gemeinsamen Ablauf verwaltet werden kann.

Vor einer möglichen späteren Weiterentwicklung der lokalen Lernplattform soll deshalb geklärt werden, ob ein plattformübergreifender Ansatz technisch machbar ist und gegenüber dem heutigen Vorgehen einen nachvollziehbaren Mehrwert bietet.

### 1.3 Zielbild

Eine Lernumgebung wird einmal fachlich beschrieben und über denselben Lebenszyklus entweder lokal oder in der Public Cloud verwaltet. Die Bedienlogik bleibt auf beiden Zielplattformen gleich, während die plattformspezifische Umsetzung klar davon getrennt ist. Der Ablauf soll reproduzierbar, messbar und ohne manuelle technische Entscheidungen funktionieren.

Der Proof of Concept schafft damit eine sachliche Entscheidungsgrundlage für eine mögliche spätere Weiterentwicklung, ohne die bestehende produktive Umgebung zu verändern.

### 1.4 Zielsetzungen und Erfolgskriterien

Die fünf Teilziele aus der bewilligten Projektbeschreibung werden als SMART-Ziele mit prüfbaren Erfolgskriterien geführt. Jedes Ziel wird in jedem Sprint Review gegen diese Tabelle abgeglichen, die Spalte Status wird dabei nachgeführt.

| ID | Ziel | Messkriterium | Zielwert | Nachweis | Status |
| --- | --- | --- | --- | --- | --- |
| Z1 | Plattformneutrales Modell für Lernumgebungen | Versioniertes YAML-Modell mit JSON-Schema, gültige Definition wird akzeptiert, ungültige abgewiesen | 1 Modell, 1 Schema, je 1 positiver und 1 negativer Testfall bestehen | Repository, Testprotokoll | Offen |
| Z2 | Zentraler Agent mit Zustandsführung | create, status, reset und delete laufen über festgelegte Zustandsübergänge, Zustand ist persistent | 4 Operationen funktionsfähig, reset erzeugt aus derselben Definition neu | Quellcode, Zustandsdiagramm, Testprotokoll | Offen |
| Z3 | On-Prem-Backend mit Kubernetes und KubeVirt | Test-Lernumgebung wird automatisiert bereitgestellt und vollständig entfernt | 3 vollständige Durchläufe ohne manuelle Korrektur | Laufprotokolle, Screenshots | Offen |
| Z4 | Bewertung der MCP-basierten Adapterarchitektur | Dieselbe Definition läuft lokal und auf genau einer Public Cloud, Bewertung gegen direkte API-Anbindung | 3 vollständige Durchläufe in der Cloud, Bewertung nach 5 Kriterien dokumentiert | Laufprotokolle, Bewertungstabelle | Offen |
| Z5 | Messbarer Vergleich mit dem heutigen Vorgehen | Bereitstellungszeit, manuelle Eingriffe, Reproduzierbarkeit, vollständiger Abbau | Vorher- und Nachher-Werte für denselben Testfall protokolliert | Messprotokoll, Vergleichstabelle | Offen |

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
| Sprachmodellbasierte Entscheidungslogik | Der Agent arbeitet nach festgelegten Regeln, das ist für die Reproduzierbarkeit zwingend |
| Bedienoberfläche | Der Nachweis erfolgt über die Kommandozeile, eine Oberfläche bringt keinen zusätzlichen Erkenntnisgewinn |
| Zweite Public Cloud | Eine Plattform genügt, um die Austauschbarkeit über die Adapterschicht zu zeigen |
| GitOps oder Argo CD | War Gegenstand der Semesterarbeit 5 und ist hier bewusst nicht Thema |
| Hochverfügbarkeit, verteilter Storage, produktive Skalierung | Betriebsthemen, die erst bei einer produktiven Einführung relevant werden |
| Hardwarebeschaffung und betriebliche Netzwerkumstellungen | Es wird ausschliesslich vorhandene, freigegebene Hardware verwendet |

Diese Punkte werden im Ausblick in Kapitel 10 behandelt.

### 1.7 Zielgruppe und Lesehinweise

Die Dokumentation richtet sich an die beiden Experten, an den Informatikdienst der TBZ und an die HF-Lehrgangsleitung. Sie ist so geschrieben, dass ein fachlich versierter Leser ohne Vorwissen über die TBZ-Umgebung folgen kann. Fachbegriffe werden im Glossar am Ende erklärt.

### 1.8 Themenfeldabdeckung

| Themenfeld | Bezug in dieser Arbeit | Kapitel |
| --- | --- | --- |
| Cloud Engineering | Entwurf und Beurteilung einer Lösung für lokale und Public-Cloud-Infrastruktur | 3, 4, 6 |
| DevOps und Automatisierung | Reproduzierbare Bereitstellung, Zustandsführung, Tests, vollständiger Abbau | 4, 5 |
| Cloud-native Virtualisierung | Betrieb virtueller Maschinen auf Kubernetes mit KubeVirt | 4 |
| Schnittstellen- und Architekturdesign | Trennung zwischen Fachmodell, zentraler Steuerung und plattformspezifischen Adaptern | 3, 4 |
| Projektmanagement | Hybrides Vorgehen mit Sprints innerhalb fixer Meilensteine | 2 |
| Wirtschaftlichkeit | Kosten-Nutzen-Betrachtung auf Basis erhobener Messwerte | 6 |
| Betrieb und Schulung | Runbook und Einführung für Nutzende | 7 |

---

## 2 Projektmanagement



## 3 Analyse und Konzept



## 4 Umsetzung



## 5 Tests und Messungen



## 6 Bewertung und Vergleich



## 7 Betrieb und Schulung



## 8 Projektverlauf



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
