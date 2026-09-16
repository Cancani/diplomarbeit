#!/usr/bin/env bash

set -euo pipefail

REPO="${1:-Cancani/diplomarbeit}"
echo "Repository: $REPO"

vorhanden="$(gh issue list --repo "$REPO" --state all --limit 300 --json title --jq '.[].title')"
angelegt=0
ignoriert=0

if grep -Fq "US01:" <<<"$vorhanden"; then
  echo "  vorhanden:  US01: Repository mit klarer Struktur"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US01: Repository mit klarer Struktur" \
    --label "story" --label "E1" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich ein Repository mit klarer Struktur, damit Code, Dokumentation und Nachweise von Beginn weg am selben Ort liegen.

| | |
| --- | --- |
| Epic | E1 Projektinitialisierung |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die Ordnerstruktur für Dokumentation, Skripte, Agent, Adapter, Modell und Infrastruktur ist angelegt
- [ ] Das README nennt Diplomand, Auftraggeber, beide Experten, Laufzeit und den Link zur Dokumentation
- [ ] Die .gitignore schliesst Build-Artefakte und Geheimnisse aus
- [ ] Der erste Commit liegt auf main

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US01: Repository mit klarer Struktur"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US02:" <<<"$vorhanden"; then
  echo "  vorhanden:  US02: Öffentlich einsehbares Project Board"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US02: Öffentlich einsehbares Project Board" \
    --label "story" --label "E1" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich ein öffentlich einsehbares Project Board, damit ich den Projektstand jederzeit ohne Rückfrage sehe.

| | |
| --- | --- |
| Epic | E1 Projektinitialisierung |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Das Board existiert und ist auf Public gestellt
- [ ] Die Felder Status, Priority, Sprint, Epic und Story Points sind vorhanden, Story Points als Zahlenfeld
- [ ] Der Workflow Auto-add für Issues des Repositories ist aktiv
- [ ] Der Zugriff wurde aus einem abgemeldeten Browser geprüft und im Statusbericht KW38 bestätigt

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US02: Öffentlich einsehbares Project Board"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US03:" <<<"$vorhanden"; then
  echo "  vorhanden:  US03: Vorlagen, Labels, Milestones und Regeln"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US03: Vorlagen, Labels, Milestones und Regeln" \
    --label "story" --label "E1" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich einheitliche Vorlagen und Schutzregeln, damit jedes Ticket denselben Qualitätsstandard erfüllt.

| | |
| --- | --- |
| Epic | E1 Projektinitialisierung |
| Story Points | 1 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Drei Issue-Vorlagen sind aktiv, leere Issues sind deaktiviert
- [ ] Die Pull-Request-Vorlage ist aktiv
- [ ] 19 Labels und drei Milestones sind angelegt
- [ ] Das Ruleset auf main ist aktiv und blockiert Force Pushes

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US03: Vorlagen, Labels, Milestones und Regeln"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US04:" <<<"$vorhanden"; then
  echo "  vorhanden:  US04: Dokumentation über GitHub Pages"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US04: Dokumentation über GitHub Pages" \
    --label "story" --label "E1" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich die Dokumentation über eine öffentliche Seite lesen, damit ich den Stand ohne Repository-Navigation verfolgen kann.

| | |
| --- | --- |
| Epic | E1 Projektinitialisierung |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Der Workflow baut die Dokumentation bei jedem Push auf main mit strikter Prüfung
- [ ] Die Seite ist öffentlich erreichbar
- [ ] Der Link wurde an beide Experten versendet
- [ ] Ein fehlerhafter Link oder eine fehlende Datei lässt den Build scheitern

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US04: Dokumentation über GitHub Pages"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US05:" <<<"$vorhanden"; then
  echo "  vorhanden:  US05: Journal und Statusbericht als feste Routine"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US05: Journal und Statusbericht als feste Routine" \
    --label "story" --label "E1" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich Journal und Statusbericht als feste Routine, damit der Projektverlauf lückenlos nachvollziehbar bleibt.

| | |
| --- | --- |
| Epic | E1 Projektinitialisierung |
| Story Points | 1 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die Vorlagen für Statusbericht und Journaleintrag liegen im Repository
- [ ] Der erste Journaleintrag ist veröffentlicht
- [ ] Der erste Statusbericht KW38 ist veröffentlicht und im Teams-Kanal verlinkt
- [ ] Die Übersichtstabelle über alle 14 Kalenderwochen ist angelegt

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US05: Journal und Statusbericht als feste Routine"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US06:" <<<"$vorhanden"; then
  echo "  vorhanden:  US06: Kickoff mit den Experten"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US06: Kickoff mit den Experten" \
    --label "story" --label "E1" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich einen Kickoff mit den Experten, damit Erwartungen, Kommunikationswege und Termine verbindlich geklärt sind.

| | |
| --- | --- |
| Epic | E1 Projektinitialisierung |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Der Kickoff wurde mit beiden Experten durchgeführt
- [ ] Die Abgrenzung ist bestätigt: genau eine Public Cloud, kein Sprachmodell in der Entscheidungslogik
- [ ] Die drei Zwischenpräsentationstermine stehen in den Kalendern aller Beteiligten
- [ ] Das Protokoll liegt im Repository, Rückmeldungen sind als Issues erfasst

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US06: Kickoff mit den Experten"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US07:" <<<"$vorhanden"; then
  echo "  vorhanden:  US07: IST-Analyse der heutigen Bereitstellung"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US07: IST-Analyse der heutigen Bereitstellung" \
    --label "story" --label "E2" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Auftraggeber** möchte ich die heutige Bereitstellung dokumentiert sehen, damit der Vergleich eine belastbare Grundlage hat.

| | |
| --- | --- |
| Epic | E2 IST-Aufnahme und Ausgangsmessung |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Der Ablauf über LernMAAS ist beschrieben, von createvms bis zur nutzbaren VM
- [ ] Die beteiligten Komponenten und Schnittstellen sind benannt
- [ ] Die manuellen Schritte sind einzeln aufgelistet und gezählt
- [ ] Quellenangaben auf mc-b/lernmaas und die Kurzanleitung TBZ-Cloud sind gesetzt

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US07: IST-Analyse der heutigen Bereitstellung"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US08:" <<<"$vorhanden"; then
  echo "  vorhanden:  US08: Test-Lernumgebung aus m239, m254 und m426 ableiten"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US08: Test-Lernumgebung aus m239, m254 und m426 ableiten" \
    --label "story" --label "E2" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich eine technisch reduzierte Test-Lernumgebung ableiten, damit der Lebenszyklus vollständig prüfbar bleibt.

| | |
| --- | --- |
| Epic | E2 IST-Aufnahme und Ausgangsmessung |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die Konfigurationsmerkmale der drei Profile sind tabellarisch erfasst
- [ ] Die Auswahl der übernommenen Merkmale ist begründet
- [ ] Die Test-Lernumgebung ist vollständig spezifiziert: Anzahl VMs, CPU, RAM, Disk, Betriebssystem, Testdienst
- [ ] Die Spezifikation ist mit dem Firmenexperten abgestimmt

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US08: Test-Lernumgebung aus m239, m254 und m426 ableiten"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US09:" <<<"$vorhanden"; then
  echo "  vorhanden:  US09: Messkonzept mit identischen Start- und Endkriterien"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US09: Messkonzept mit identischen Start- und Endkriterien" \
    --label "story" --label "E2" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich ein Messkonzept mit identischen Start- und Endkriterien, damit der Vorher-Nachher-Vergleich aussagekräftig ist.

| | |
| --- | --- |
| Epic | E2 IST-Aufnahme und Ausgangsmessung |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Start- und Endkriterium sind für beide Vorgehensweisen identisch definiert
- [ ] Die Messgrössen sind festgelegt: Bereitstellungszeit, Anzahl manueller Eingriffe, Reproduzierbarkeit, vollständiger Abbau
- [ ] Das Endkriterium des Abbaus ist das nachgewiesene Verschwinden aller Ressourcen inklusive PersistentVolume, nicht der abgesetzte Befehl
- [ ] Der Umgang mit dem Image-Import ist geregelt, damit nicht die Internetanbindung gemessen wird
- [ ] Die unterschiedliche Hardware beider Umgebungen ist als Einschränkung erklärt, die tragende Messgrösse ist hardwareunabhängig
- [ ] Die Zeit ist in Bearbeitungszeit der Person und Wartezeit des Systems aufgeteilt
- [ ] Die Messprotokollvorlage liegt im Repository

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US09: Messkonzept mit identischen Start- und Endkriterien"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US10:" <<<"$vorhanden"; then
  echo "  vorhanden:  US10: Ausgangsmessung am heutigen Vorgehen"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US10: Ausgangsmessung am heutigen Vorgehen" \
    --label "story" --label "E2" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Auftraggeber** möchte ich eine Ausgangsmessung am heutigen Vorgehen, damit der Nutzen später beziffert werden kann.

| | |
| --- | --- |
| Epic | E2 IST-Aufnahme und Ausgangsmessung |
| Story Points | 5 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Eine freie VPN-Umgebung ist reserviert und in der Reservationsliste eingetragen, kein laufender Unterricht ist betroffen
- [ ] Mindestens ein vollständiger Durchlauf nach Messkonzept ist protokolliert
- [ ] Bereitstellungszeit und Anzahl manueller Eingriffe sind erfasst, die manuellen Schritte sind einzeln aufgeführt
- [ ] Infrastrukturelle Unterschiede zum Proof of Concept sind separat ausgewiesen
- [ ] Keine Zugangsdaten, insbesondere keine privaten WireGuard-Schlüssel, sind in der Dokumentation abgebildet
- [ ] Das Messprotokoll liegt im Repository

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US10: Ausgangsmessung am heutigen Vorgehen"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US11:" <<<"$vorhanden"; then
  echo "  vorhanden:  US11: Hardware betriebsbereit und dokumentiert"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US11: Hardware betriebsbereit und dokumentiert" \
    --label "story" --label "E3" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich die freigegebene Hardware betriebsbereit und dokumentiert haben, damit die Umsetzung nicht an der Grundkonfiguration scheitert.

| | |
| --- | --- |
| Epic | E3 On-Prem Plattform |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] dl380-01 und die fünf HP-Rechner sind erreichbar und in einer Tabelle dokumentiert
- [ ] Virtualisierungsunterstützung ist geprüft, vmx vorhanden und kvm geladen
- [ ] Die Netzwerkanbindung ist dokumentiert, inklusive Switch 10.0.26.0/24
- [ ] Die bestehende Nutzung ist geprüft, es gibt keine Kollision mit dem Unterricht

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US11: Hardware betriebsbereit und dokumentiert"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US12:" <<<"$vorhanden"; then
  echo "  vorhanden:  US12: Kubernetes-Cluster verifizieren und dokumentieren"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US12: Kubernetes-Cluster verifizieren und dokumentieren" \
    --label "story" --label "E3" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich den Zustand des Kubernetes-Clusters kennen und dokumentiert haben, damit die On-Prem-Zielplattform als Ausgangspunkt feststeht.

| | |
| --- | --- |
| Epic | E3 On-Prem Plattform |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Der Ist-Zustand ist dokumentiert: MicroK8s-Version, Addons, Storage-Klassen, CNI
- [ ] Der Cluster ist als übernommene Vorarbeit gekennzeichnet, mit Datum der Ersteinrichtung
- [ ] Die Verifikation ist dokumentiert: Knoten im Zustand Ready, API erreichbar
- [ ] Der Entscheid für dl380-01 als Zielplattform ist als ADR begründet

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US12: Kubernetes-Cluster verifizieren und dokumentieren"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US13:" <<<"$vorhanden"; then
  echo "  vorhanden:  US13: KubeVirt verifizieren und Storage klären"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US13: KubeVirt verifizieren und Storage klären" \
    --label "story" --label "E3" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich KubeVirt als nutzbare Virtualisierungsschicht bestätigt haben, damit virtuelle Maschinen als Kubernetes-Ressourcen verwaltet werden können.

| | |
| --- | --- |
| Epic | E3 On-Prem Plattform |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] KubeVirt im Zustand Deployed ist nachgewiesen, CDI ist vorhanden, virtctl ist verfügbar
- [ ] Die verfügbaren Storage-Klassen sind dokumentiert und die Wahl ist begründet
- [ ] Die Netzanbindung der VMs ist dokumentiert
- [ ] Der Bestand ist als übernommene Vorarbeit gekennzeichnet

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US13: KubeVirt verifizieren und Storage klären"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US38:" <<<"$vorhanden"; then
  echo "  vorhanden:  US38: Referenz-VM manuell erstellen und wieder abbauen"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US38: Referenz-VM manuell erstellen und wieder abbauen" \
    --label "story" --label "E3" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich eine Referenz-VM von Hand durch den vollständigen Lebenszyklus führen, damit ich weiss, welche Ressourcen mein Adapter später erzeugen muss.

| | |
| --- | --- |
| Epic | E3 On-Prem Plattform |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die VM ist über ein KubeVirt-Manifest erstellt, gestartet und erreichbar
- [ ] Der Testdienst antwortet über den definierten Zugriffsweg
- [ ] Die Bereitstellungszeit ist gemessen und protokolliert
- [ ] Der vollständige Abbau ist durchgeführt und die Restfreiheit ist geprüft
- [ ] Die fachlichen und die technischen Felder des Manifests sind getrennt aufgelistet

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US38: Referenz-VM manuell erstellen und wieder abbauen"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US14:" <<<"$vorhanden"; then
  echo "  vorhanden:  US14: Auswahl der Public Cloud als Nutzwertanalyse"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US14: Auswahl der Public Cloud als Nutzwertanalyse" \
    --label "story" --label "E4" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich die Public-Cloud-Plattform anhand nachvollziehbarer Kriterien auswählen, damit der Entscheid begründet und nicht zufällig ist.

| | |
| --- | --- |
| Epic | E4 Public Cloud |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die Bewertungskriterien sind vorab festgelegt und gewichtet
- [ ] Mindestens zwei Plattformen sind bewertet
- [ ] Der Entscheid ist als ADR dokumentiert, inklusive Begründung der Gewichtung

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US14: Auswahl der Public Cloud als Nutzwertanalyse"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US15:" <<<"$vorhanden"; then
  echo "  vorhanden:  US15: Cloud-Smoke-Test mit Budgetwarnung und Quotas"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US15: Cloud-Smoke-Test mit Budgetwarnung und Quotas" \
    --label "story" --label "E4" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich einen minimalen Cloud-Smoke-Test durchführen, damit Quotas, Dienstverfügbarkeit und Kostenkontrolle früh geklärt sind.

| | |
| --- | --- |
| Epic | E4 Public Cloud |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Das Konto ist eingerichtet und der Zugang funktioniert
- [ ] Budgetwarnungen bei CHF 25 und CHF 40 sind gesetzt
- [ ] Quotas und Dienstverfügbarkeit sind geprüft
- [ ] Eine minimale VM ist erstellt, erreicht und sofort wieder gelöscht, die Kosten sind protokolliert

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US15: Cloud-Smoke-Test mit Budgetwarnung und Quotas"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US16:" <<<"$vorhanden"; then
  echo "  vorhanden:  US16: Zielarchitektur, ADRs und Zwischenpräsentation 1"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US16: Zielarchitektur, ADRs und Zwischenpräsentation 1" \
    --label "story" --label "E11" --label "must" \
    --milestone "Sprint 1" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich die Zielarchitektur und die zentralen Entscheide präsentiert bekommen, damit ich die Richtung vor der Umsetzung beurteilen kann.

| | |
| --- | --- |
| Epic | E11 Architektur und Projektabschluss |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 1 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die Architektur ist mit Systemkontext und Komponentensicht dokumentiert
- [ ] Mindestens drei Architekturentscheide sind als ADR festgehalten
- [ ] Die Zwischenpräsentation 1 ist durchgeführt
- [ ] Die Rückmeldungen sind protokolliert und als Issues erfasst

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US16: Zielarchitektur, ADRs und Zwischenpräsentation 1"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US17:" <<<"$vorhanden"; then
  echo "  vorhanden:  US17: Plattformneutrales YAML-Modell für Lernumgebungen"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US17: Plattformneutrales YAML-Modell für Lernumgebungen" \
    --label "story" --label "E5" --label "must" \
    --milestone "Sprint 2" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Dozent** möchte ich eine Lernumgebung einmal fachlich beschreiben, damit ich sie nicht pro Plattform neu definieren muss.

| | |
| --- | --- |
| Epic | E5 Fachmodell |
| Story Points | 5 |
| Priorität | MUST |
| Sprint | 2 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Das Modell beschreibt die benötigten VMs und den zu prüfenden Testdienst plattformunabhängig
- [ ] Die Modellversion ist in der Datei geführt
- [ ] Alle in US38 ermittelten fachlichen Felder sind abgedeckt
- [ ] Mindestens eine vollständige Beispieldefinition liegt vor
- [ ] Das Modell enthält keine plattformspezifischen Begriffe

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US17: Plattformneutrales YAML-Modell für Lernumgebungen"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US18:" <<<"$vorhanden"; then
  echo "  vorhanden:  US18: JSON-Schema mit positiver und negativer Validierung"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US18: JSON-Schema mit positiver und negativer Validierung" \
    --label "story" --label "E5" --label "must" \
    --milestone "Sprint 2" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich fehlerhafte Definitionen automatisch abweisen, damit fachliche Fehler nicht erst in der Infrastruktur auffallen.

| | |
| --- | --- |
| Epic | E5 Fachmodell |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 2 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Das Schema ist versioniert und passt zum Modell
- [ ] Eine gültige Definition wird akzeptiert
- [ ] Eine bewusst ungültige Definition wird mit verständlicher Fehlermeldung abgewiesen
- [ ] Beide Fälle laufen als automatisierter Test

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US18: JSON-Schema mit positiver und negativer Validierung"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US19:" <<<"$vorhanden"; then
  echo "  vorhanden:  US19: Agent-Grundgerüst mit Kommandozeilenschnittstelle"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US19: Agent-Grundgerüst mit Kommandozeilenschnittstelle" \
    --label "story" --label "E6" --label "must" \
    --milestone "Sprint 2" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich ein Agent-Grundgerüst mit Kommandozeilenschnittstelle, damit alle Operationen einheitlich aufgerufen werden.

| | |
| --- | --- |
| Epic | E6 Agent |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 2 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] create, status, reset und delete sind aufrufbar
- [ ] Die Konfiguration liegt ausserhalb des Codes, es sind keine Geheimnisse im Repository
- [ ] Hilfe- und Fehlerausgaben sind verständlich
- [ ] Das Grundgerüst ist durch Tests abgedeckt

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US19: Agent-Grundgerüst mit Kommandozeilenschnittstelle"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US20:" <<<"$vorhanden"; then
  echo "  vorhanden:  US20: Persistenter Zustandsspeicher mit Zustandsübergängen"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US20: Persistenter Zustandsspeicher mit Zustandsübergängen" \
    --label "story" --label "E6" --label "must" \
    --milestone "Sprint 2" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich einen persistenten Zustandsspeicher mit definierten Zustandsübergängen, damit gleiche Eingaben zur gleichen nächsten Aktion führen.

| | |
| --- | --- |
| Epic | E6 Agent |
| Story Points | 5 |
| Priorität | MUST |
| Sprint | 2 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Das Zustandsdiagramm ist dokumentiert
- [ ] Der Zustand überlebt einen Neustart des Agenten
- [ ] Unzulässige Zustandsübergänge werden abgewiesen
- [ ] Gleiche gültige Eingabe und gleicher Zustand führen zur gleichen nächsten Aktion
- [ ] Das Warten auf den Endzustand mit Zeitbegrenzung ist implementiert

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US20: Persistenter Zustandsspeicher mit Zustandsübergängen"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US21:" <<<"$vorhanden"; then
  echo "  vorhanden:  US21: create und status"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US21: create und status" \
    --label "story" --label "E6" --label "must" \
    --milestone "Sprint 2" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Dozent** möchte ich eine Lernumgebung mit einem Befehl erstellen und ihren Zustand abfragen, damit ich keine technischen Einzelschritte ausführen muss.

| | |
| --- | --- |
| Epic | E6 Agent |
| Story Points | 5 |
| Priorität | MUST |
| Sprint | 2 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] create erzeugt die Umgebung aus der Definition
- [ ] Alle erzeugten Ressourcen tragen eine eindeutige Laufkennzeichnung
- [ ] status liest den tatsächlichen Zustand von der Plattform statt ihn anzunehmen
- [ ] Ein wiederholtes create im gleichen Zustand erzeugt keine Dubletten

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US21: create und status"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US22:" <<<"$vorhanden"; then
  echo "  vorhanden:  US22: reset und delete"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US22: reset und delete" \
    --label "story" --label "E6" --label "must" \
    --milestone "Sprint 2" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Dozent** möchte ich eine Lernumgebung zurücksetzen und vollständig entfernen, damit keine Reste zurückbleiben.

| | |
| --- | --- |
| Epic | E6 Agent |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 2 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] delete entfernt alle dem Lauf zugeordneten Ressourcen
- [ ] reset löscht die Umgebung und erstellt sie aus derselben Definition neu
- [ ] Beide Operationen sind wiederholbar

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US22: reset und delete"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US23:" <<<"$vorhanden"; then
  echo "  vorhanden:  US23: Einheitliches Funktionsset über MCP"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US23: Einheitliches Funktionsset über MCP" \
    --label "story" --label "E7" --label "must" \
    --milestone "Sprint 2" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich ein einheitliches Funktionsset über MCP definieren, damit Zielplattformen austauschbar bleiben.

| | |
| --- | --- |
| Epic | E7 MCP-Adapter |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 2 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die gemeinsamen Funktionen und ihre Signaturen sind dokumentiert
- [ ] Die Fehlerfälle sind Teil des Vertrags
- [ ] Die Trennung zwischen Agent und Adapter ist im Code sichtbar
- [ ] Ein Fake-Adapter implementiert den Vertrag und ermöglicht Tests ohne Infrastruktur

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US23: Einheitliches Funktionsset über MCP"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US24:" <<<"$vorhanden"; then
  echo "  vorhanden:  US24: MCP-Adapter für KubeVirt, erster End-to-End-Durchlauf"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US24: MCP-Adapter für KubeVirt, erster End-to-End-Durchlauf" \
    --label "story" --label "E7" --label "must" \
    --milestone "Sprint 2" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich einen MCP-Adapter für KubeVirt, damit die Test-Lernumgebung lokal aus der gemeinsamen Definition entsteht.

| | |
| --- | --- |
| Epic | E7 MCP-Adapter |
| Story Points | 5 |
| Priorität | MUST |
| Sprint | 2 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Der Adapter erzeugt aus der Modelldefinition die benötigten KubeVirt-Ressourcen
- [ ] Ein vollständiger Durchlauf läuft lokal ohne manuellen Eingriff
- [ ] Die Readiness wird geprüft
- [ ] Der Abbau ist vollständig

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US24: MCP-Adapter für KubeVirt, erster End-to-End-Durchlauf"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US25:" <<<"$vorhanden"; then
  echo "  vorhanden:  US25: MCP-Adapter für die Public Cloud"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US25: MCP-Adapter für die Public Cloud" \
    --label "story" --label "E7" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Auftraggeber** möchte ich dieselbe Definition auch in der Public Cloud ausführen lassen, damit die Plattformunabhängigkeit belegt ist.

| | |
| --- | --- |
| Epic | E7 MCP-Adapter |
| Story Points | 8 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Das benötigte Netzwerk in der Cloud ist angelegt oder ausgewählt, der Testdienst ist erreichbar
- [ ] Der Adapter erzeugt aus derselben Modelldefinition die Cloud-Ressourcen
- [ ] Ein vollständiger Durchlauf mit create, status, reset und delete läuft ohne manuellen Eingriff
- [ ] Die Kosten pro Durchlauf sind protokolliert

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US25: MCP-Adapter für die Public Cloud"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US26:" <<<"$vorhanden"; then
  echo "  vorhanden:  US26: Automatisierter Readiness-Check"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US26: Automatisierter Readiness-Check" \
    --label "story" --label "E8" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Diplomand** möchte ich einen automatisierten Readiness-Check, damit der Erfolg eines Laufs nicht von einer Sichtprüfung abhängt.

| | |
| --- | --- |
| Epic | E8 Validierung und Messung |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Der Check prüft automatisiert, ob die VM läuft und der Testdienst antwortet
- [ ] Das Ergebnis ist maschinenlesbar protokolliert
- [ ] Der Check funktioniert auf beiden Zielplattformen
- [ ] Zeitbegrenzung und Wiederholung sind definiert

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US26: Automatisierter Readiness-Check"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US27:" <<<"$vorhanden"; then
  echo "  vorhanden:  US27: Drei vollständige Durchläufe auf der lokalen Plattform"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US27: Drei vollständige Durchläufe auf der lokalen Plattform" \
    --label "story" --label "E8" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich drei aufeinanderfolgende vollständige Durchläufe lokal sehen, damit die Reproduzierbarkeit belegt ist.

| | |
| --- | --- |
| Epic | E8 Validierung und Messung |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Drei Durchläufe laufen ohne manuelle Korrektur
- [ ] Zeiten und manuelle Eingriffe sind je Durchlauf protokolliert
- [ ] Die Laufprotokolle liegen im Repository

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US27: Drei vollständige Durchläufe auf der lokalen Plattform"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US28:" <<<"$vorhanden"; then
  echo "  vorhanden:  US28: Drei vollständige Durchläufe in der Public Cloud"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US28: Drei vollständige Durchläufe in der Public Cloud" \
    --label "story" --label "E8" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich dieselben drei Durchläufe in der Public Cloud sehen, damit der Nachweis auf beiden Plattformen gleichwertig ist.

| | |
| --- | --- |
| Epic | E8 Validierung und Messung |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Drei Durchläufe laufen ohne manuelle Korrektur
- [ ] Zeiten, manuelle Eingriffe und Kosten sind je Durchlauf protokolliert
- [ ] Die Laufprotokolle liegen im Repository

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US28: Drei vollständige Durchläufe in der Public Cloud"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US29:" <<<"$vorhanden"; then
  echo "  vorhanden:  US29: Nachweis des vollständigen Abbaus"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US29: Nachweis des vollständigen Abbaus" \
    --label "story" --label "E8" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Auftraggeber** möchte ich den vollständigen Abbau nachgewiesen sehen, damit keine Kosten und keine Altlasten zurückbleiben.

| | |
| --- | --- |
| Epic | E8 Validierung und Messung |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Nach jedem delete sind keine dem Lauf zugeordneten Ressourcen mehr auffindbar
- [ ] Die Prüfung läuft automatisiert und wartet auf den Endzustand
- [ ] Auch verzögert entfernte Ressourcen wie PersistentVolumes sind erfasst
- [ ] Das Ergebnis ist je Durchlauf protokolliert

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US29: Nachweis des vollständigen Abbaus"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US30:" <<<"$vorhanden"; then
  echo "  vorhanden:  US30: Vorher-Nachher-Vergleich"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US30: Vorher-Nachher-Vergleich" \
    --label "story" --label "E9" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Auftraggeber** möchte ich den Vergleich zum heutigen Vorgehen in Zahlen, damit ich den Nutzen beurteilen kann.

| | |
| --- | --- |
| Epic | E9 Bewertung und Vergleich |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Vorher- und Nachher-Werte sind für denselben Testfall gegenübergestellt
- [ ] Infrastrukturelle Unterschiede sind separat ausgewiesen
- [ ] Die Aussagegrenzen des Vergleichs sind benannt

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US30: Vorher-Nachher-Vergleich"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US31:" <<<"$vorhanden"; then
  echo "  vorhanden:  US31: Bewertung der MCP-Architektur gegen eine direkte API-Anbindung"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US31: Bewertung der MCP-Architektur gegen eine direkte API-Anbindung" \
    --label "story" --label "E9" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich die MCP-Adapterarchitektur gegen eine direkte API-Anbindung bewertet sehen, damit der architektonische Mehrwert belegt ist.

| | |
| --- | --- |
| Epic | E9 Bewertung und Vergleich |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die Bewertung erfolgt als Nutzwertanalyse über Kopplung, Aufwand, Testbarkeit, Fehlerbehandlung und Erweiterbarkeit
- [ ] Die Gewichtung ist vor der Bewertung festgelegt und begründet
- [ ] Jedes Kriterium ist mit einem Beispiel aus der Umsetzung belegt

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US31: Bewertung der MCP-Architektur gegen eine direkte API-Anbindung"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US32:" <<<"$vorhanden"; then
  echo "  vorhanden:  US32: Wirtschaftlichkeitsbetrachtung"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US32: Wirtschaftlichkeitsbetrachtung" \
    --label "story" --label "E9" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Auftraggeber** möchte ich eine Wirtschaftlichkeitsbetrachtung, damit ich über eine Weiterentwicklung entscheiden kann.

| | |
| --- | --- |
| Epic | E9 Bewertung und Vergleich |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Kosten und Nutzen sind auf Basis der erhobenen Messwerte gegenübergestellt
- [ ] Ressourcen, Nachhaltigkeit und Skalierbarkeit sind bewertet
- [ ] Der Einmalaufwand ist aus der Zeiterfassung des Journals abgeleitet

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US32: Wirtschaftlichkeitsbetrachtung"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US33:" <<<"$vorhanden"; then
  echo "  vorhanden:  US33: Beurteilung der Übertragbarkeit in den Produktivbetrieb"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US33: Beurteilung der Übertragbarkeit in den Produktivbetrieb" \
    --label "story" --label "E9" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Auftraggeber** möchte ich wissen, was von diesem Proof of Concept übertragbar wäre, damit die Entscheidungsgrundlage vollständig ist.

| | |
| --- | --- |
| Epic | E9 Bewertung und Vergleich |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Jede Komponente ist hinsichtlich Übertragbarkeit beurteilt
- [ ] Offene Punkte für Sicherheit, Berechtigungen, Monitoring, Skalierbarkeit und Betriebsprozesse sind benannt
- [ ] Die Zuständigkeitsmatrix aus Kapitel 2.2.1 ist mit einem begründeten Vorschlag gefüllt
- [ ] Der Vorschlag ist mit beiden Experten abgestimmt

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US33: Beurteilung der Übertragbarkeit in den Produktivbetrieb"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US34:" <<<"$vorhanden"; then
  echo "  vorhanden:  US34: Runbook für Aufbau, Bedienung, Fehleranalyse und Abbau"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US34: Runbook für Aufbau, Bedienung, Fehleranalyse und Abbau" \
    --label "story" --label "E10" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Betreiber** möchte ich ein Runbook, damit ich die Umgebung ohne den Diplomanden betreiben kann.

| | |
| --- | --- |
| Epic | E10 Betrieb und Schulung |
| Story Points | 2 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Das Runbook deckt Aufbau, Bedienung, Fehleranalyse und vollständigen Abbau ab
- [ ] Die Schritte wurden einmal von Anfang bis Ende nachvollzogen
- [ ] Typische Fehlerbilder sind mit Ursache und Behebung erfasst

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US34: Runbook für Aufbau, Bedienung, Fehleranalyse und Abbau"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US35:" <<<"$vorhanden"; then
  echo "  vorhanden:  US35: Schulungsunterlage und Einführung"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US35: Schulungsunterlage und Einführung" \
    --label "story" --label "E10" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Dozent** möchte ich eine kurze Einführung und Unterlage, damit ich die Lösung ohne Vorwissen benutzen kann.

| | |
| --- | --- |
| Epic | E10 Betrieb und Schulung |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Die Schulungsunterlage beschreibt den Ablauf und die typischen Fehler
- [ ] Eine Einführung wurde mit mindestens einer Person durchgeführt
- [ ] Die Rückmeldung ist eingearbeitet

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US35: Schulungsunterlage und Einführung"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US36:" <<<"$vorhanden"; then
  echo "  vorhanden:  US36: Dokumentation finalisieren, Management Summary, Ehrenwort"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US36: Dokumentation finalisieren, Management Summary, Ehrenwort" \
    --label "story" --label "E11" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich eine vollständige, sequentiell lesbare Dokumentation, damit ich die Arbeit ohne Medienbrüche beurteilen kann.

| | |
| --- | --- |
| Epic | E11 Architektur und Projektabschluss |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Alle Kapitel sind gefüllt, es gibt keine Platzhalter mehr
- [ ] Das Management Summary ist verfasst
- [ ] Das unterschriebene Ehrenwort liegt bei
- [ ] Quellen-, Abbildungs- und Glossarverzeichnis sind vollständig
- [ ] Die Abgabebestätigung ist an admin.wb@tbz.zh.ch versendet

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US36: Dokumentation finalisieren, Management Summary, Ehrenwort"
  angelegt=$((angelegt+1))
fi

if grep -Fq "US37:" <<<"$vorhanden"; then
  echo "  vorhanden:  US37: Kolloquiumspräsentation und Demo-Skript"
  ignoriert=$((ignoriert+1))
else
  gh issue create --repo "$REPO" \
    --title "US37: Kolloquiumspräsentation und Demo-Skript" \
    --label "story" --label "E11" --label "must" \
    --milestone "Sprint 3" \
    --body "$(cat <<'ISSUEBODY'
## User Story

Als **Experte** möchte ich eine vorbereitete Präsentation mit funktionierender Demo, damit das Kolloquium ohne Störungen abläuft.

| | |
| --- | --- |
| Epic | E11 Architektur und Projektabschluss |
| Story Points | 3 |
| Priorität | MUST |
| Sprint | 3 |

## Definition of Ready

- [x] Nutzen und Ziel sind formuliert
- [x] Akzeptanzkriterien sind prüfbar
- [x] Story Points geschätzt, Epic und Sprint zugeordnet
- [ ] Abhängigkeiten und Vorbedingungen sind geklärt

## Akzeptanzkriterien

- [ ] Der Foliensatz ist fertig und hell gestaltet
- [ ] Das Demo-Skript liegt vor, jeder Befehl ist ausgeschrieben
- [ ] Ein Backup-Plan mit aufgezeichnetem Durchlauf existiert
- [ ] Die Generalprobe wurde durchgeführt und die Demo passt in 15 Minuten
- [ ] Raum und Termin sind im Sekretariat reserviert

## Definition of Done

- [ ] Akzeptanzkriterien erfüllt
- [ ] Änderungen sind auf main
- [ ] Dokumentationsabschnitt geschrieben oder aktualisiert
- [ ] Nachweis ist in der Dokumentation platziert
- [ ] Wiederholbar anhand der Dokumentation
- [ ] Keine Geheimnisse im Repository
- [ ] Issue im Board auf Done

ISSUEBODY
    )" >/dev/null
  echo "  angelegt:   US37: Kolloquiumspräsentation und Demo-Skript"
  angelegt=$((angelegt+1))
fi

echo
echo "Angelegt: $angelegt, übersprungen: $ignoriert"
echo "Gesamt im Repository: $(gh issue list --repo "$REPO" --state all --limit 300 --json title --jq 'length')"
echo
echo "Nächster Schritt: Issues im Project Board den Feldern Sprint, Epic, Story Points und Priority zuordnen."
