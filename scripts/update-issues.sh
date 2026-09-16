#!/usr/bin/env bash

set -euo pipefail

REPO="${1:-Cancani/diplomarbeit}"
echo "Repository: $REPO"
echo

liste="$(gh issue list --repo "$REPO" --state all --limit 300 --json number,title --jq '.[] | "\(.number)|\(.title)"')"
aktualisiert=0
fehlend=0

nummer_fuer() {
  grep -m1 -E "^[0-9]+\|$1:" <<<"$liste" | cut -d"|" -f1
}

nr="$(nummer_fuer "US01")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US01"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US01: Repository mit klarer Struktur"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US02")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US02"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US02: Öffentlich einsehbares Project Board"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US03")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US03"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US03: Vorlagen, Labels, Milestones und Regeln"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US04")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US04"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US04: Dokumentation über GitHub Pages"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US05")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US05"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US05: Journal und Statusbericht als feste Routine"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US06")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US06"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US06: Kickoff mit den Experten"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US07")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US07"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US07: IST-Analyse der heutigen Bereitstellung"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US08")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US08"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US08: Test-Lernumgebung aus m239, m254 und m426 ableiten"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US09")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US09"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US09: Messkonzept mit identischen Start- und Endkriterien"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US10")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US10"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US10: Ausgangsmessung am heutigen Vorgehen"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US11")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US11"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US11: Hardware betriebsbereit und dokumentiert"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US12")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US12"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US12: Kubernetes-Cluster verifizieren und dokumentieren"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US13")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US13"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US13: KubeVirt verifizieren und Storage klären"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US38")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US38"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US38: Referenz-VM manuell erstellen und wieder abbauen"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US14")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US14"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US14: Auswahl der Public Cloud als Nutzwertanalyse"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US15")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US15"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US15: Cloud-Smoke-Test mit Budgetwarnung und Quotas"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US16")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US16"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US16: Zielarchitektur, ADRs und Zwischenpräsentation 1"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US17")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US17"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US17: Plattformneutrales YAML-Modell für Lernumgebungen"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US18")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US18"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US18: JSON-Schema mit positiver und negativer Validierung"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US19")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US19"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US19: Agent-Grundgerüst mit Kommandozeilenschnittstelle"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US20")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US20"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US20: Persistenter Zustandsspeicher mit Zustandsübergängen"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US21")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US21"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US21: create und status"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US22")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US22"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US22: reset und delete"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US23")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US23"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US23: Einheitliches Funktionsset über MCP"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US24")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US24"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US24: MCP-Adapter für KubeVirt, erster End-to-End-Durchlauf"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US25")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US25"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US25: MCP-Adapter für die Public Cloud"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US26")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US26"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US26: Automatisierter Readiness-Check"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US27")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US27"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US27: Drei vollständige Durchläufe auf der lokalen Plattform"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US28")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US28"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US28: Drei vollständige Durchläufe in der Public Cloud"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US29")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US29"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US29: Nachweis des vollständigen Abbaus"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US30")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US30"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US30: Vorher-Nachher-Vergleich"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US31")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US31"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US31: Bewertung der MCP-Architektur gegen eine direkte API-Anbindung"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US32")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US32"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US32: Wirtschaftlichkeitsbetrachtung"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US33")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US33"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US33: Beurteilung der Übertragbarkeit in den Produktivbetrieb"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US34")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US34"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US34: Runbook für Aufbau, Bedienung, Fehleranalyse und Abbau"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US35")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US35"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US35: Schulungsunterlage und Einführung"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US36")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US36"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US36: Dokumentation finalisieren, Management Summary, Ehrenwort"
  aktualisiert=$((aktualisiert+1))
fi

nr="$(nummer_fuer "US37")"
if [[ -z "$nr" ]]; then
  echo "  fehlt:        US37"
  fehlend=$((fehlend+1))
else
  gh issue edit "$nr" --repo "$REPO" --body "$(cat <<'ISSUEBODY'
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
  echo "  aktualisiert: #$nr  US37: Kolloquiumspräsentation und Demo-Skript"
  aktualisiert=$((aktualisiert+1))
fi

echo
echo "Aktualisiert: $aktualisiert, nicht gefunden: $fehlend"
