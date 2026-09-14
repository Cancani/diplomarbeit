# Diplomarbeit ITCNE24: Agentenbasierte Hybrid-Cloud-Bereitstellung von Lernumgebungen

Proof of Concept zur plattformübergreifenden Bereitstellung von Lernumgebungen mit Kubernetes, KubeVirt und MCP.

| | |
| --- | --- |
| Diplomand | Efekan Demirci, ITCNE24, TBZ Höhere Fachschule |
| Auftraggeber | Technische Berufsschule Zürich, Informatikdienst |
| Firmenexperte | Kuno Vogt, Leiter Informatikdienst TBZ |
| Schulexperte | Thanam Pangri, HF-Lehrgangsleitung |
| Laufzeit | 14.09.2026 bis 18.12.2026 |
| Abgabe | 18.12.2026 |
| Dokumentation | https://cancani.com/diplomarbeit/ |

## Aufbau des Repositories

| Pfad | Inhalt |
| --- | --- |
| `docs/dokumentation.md` | Die vollständige Dokumentation der Diplomarbeit, eine einzige Datei, sequentiell lesbar |
| `docs/status/` | Wöchentliche Statusberichte, eine Datei pro Kalenderwoche |
| `docs/journal/` | Fortlaufendes Projektjournal, eine Datei pro Monat |
| `docs/img/` | Screenshots und Nachweise |
| `docs/messungen/` | Messprotokolle der Testläufe |
| `scripts/` | Hilfsskripte für Setup und Betrieb |

Statusberichte und Journal liegen bewusst ausserhalb der Hauptdatei. Sie wachsen über vierzehn Wochen und würden die Dokumentation sonst unlesbar machen. Beide sind aus Kapitel 2 heraus verlinkt.

## Zugriff für die Experten

Repository, Dokumentation und Project Board sind öffentlich. Die Dokumentation wird bei jedem Push auf `main` automatisch neu gebaut und veröffentlicht.

## Lokale Vorschau

```bash
pip install mkdocs-material
mkdocs serve
# http://127.0.0.1:8000
```

## Arbeitsweise

- Ein Issue pro User Story, mit Akzeptanzkriterien und Definition of Done als Checkboxen
- Ein Feature Branch pro Issue, Squash Merge nach `main` über Pull Request
- Commit Konvention: `type(scope): beschreibung`, zum Beispiel `feat(agent): create implementiert`
- Nachweise entstehen mit der Umsetzung, nicht nachträglich
- Wöchentlicher Statusbericht jeden Freitag, Journaleintrag laufend
