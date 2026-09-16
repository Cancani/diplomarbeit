# Messprotokoll, Vorlage

Diese Vorlage wird für jeden Durchlauf einmal kopiert und ausgefüllt.
Dateiname: `<vorgehen>-<nummer>.md`, zum Beispiel `lernmaas-01.md` oder `poc-kubevirt-02.md`.

Grundlage ist das Messkonzept in Kapitel 3.4 der Dokumentation.

## Kopfdaten

| Feld | Wert |
| --- | --- |
| Kennung des Laufs | |
| Vorgehensweise | heutiges Vorgehen über LernMAAS / Proof of Concept |
| Zielplattform | |
| Umgebung, System und Netz | |
| Hardware | |
| Datum | |
| Ausführende Person | |
| Abbild lokal vorhanden zu Messbeginn | ja / nein, bei nein: Begründung |

## Startkriterium

- [ ] Die Anforderung der Lernumgebung liegt vor
- [ ] Die Zielumgebung ist leer, keine Vorarbeit ist geleistet
- [ ] Zeitstempel Start: 

## Schrittliste

Jeder Schritt einzeln. `M` bedeutet manueller Schritt einer Person, `A` bedeutet automatisch ablaufend.

| Nr | Beschreibung des Schritts | Art | Beginn | Ende | Dauer in s |
| --- | --- | --- | --- | --- | --- |
| 1 | | M / A | | | |
| 2 | | M / A | | | |
| 3 | | M / A | | | |

## Endkriterium Aufbau

- [ ] Der definierte Testdienst antwortet über das Netz
- [ ] Zeitstempel Ende Aufbau: 
- [ ] Nachweis der Antwort, Ausgabe oder Screenshot: 

## Auswertung Aufbau

| Grösse | Wert |
| --- | --- |
| Anzahl manueller Schritte | |
| Bearbeitungszeit der Person in s | |
| Wartezeit des Systems in s | |
| Gesamtdauer in s | |
| Manuelle Korrekturen, Anzahl | |
| Manuelle Korrekturen, Beschreibung | |

## Abbau

| Feld | Wert |
| --- | --- |
| Zeitstempel Löschbefehl abgesetzt | |
| Zeitstempel letzte Ressource verschwunden | |
| Verbliebene Ressourcen nach Ablauf der Wartezeit | keine / Auflistung |
| Prüfbefehl und Ausgabe | |

- [ ] Endkriterium Abbau erfüllt: keine dem Lauf zugeordnete Ressource mehr vorhanden, PersistentVolume eingeschlossen

## Bemerkungen und Auffälligkeiten

## Hinweis

In diesem Protokoll werden keine Zugangsdaten festgehalten, insbesondere keine privaten Schlüssel.
