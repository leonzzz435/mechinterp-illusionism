# Arbeitsrechner: standardisierte Baseline v1

**Diese Anleitung ist der nächste Arbeitsauftrag. Die alten großen Sweeps bleiben gestoppt.**

Wir prüfen mit EleutherAIs `lm-evaluation-harness==0.4.13`, ob Gemma die drei Aufgabenfamilien zuverlässig löst. Das Harness übernimmt Prompt-Aufbau, Tokenisierung, vollständige Antwort-Log-Likelihoods und Accuracy. Unser Code liefert Aufgaben, überprüft die gespeicherten Ergebnisse und organisiert fortsetzbare Blöcke.

## 1. Aktualisieren und ausführen

Im bestehenden Repository unter Linux/WSL auf dem Blackwell-Rechner:

```bash
git pull --ff-only origin main
uv sync --locked --extra gpu --extra eval
uv run --extra gpu --extra eval self-study-harness validate configs/harness-baseline.json
uv run --extra gpu --extra eval self-study-harness run configs/harness-baseline.json --out runs/harness-baseline-v1
uv run --extra gpu --extra eval self-study-harness export runs/harness-baseline-v1 --out exports/harness-baseline-v1.tar.gz
```

Erwartete Vorabprüfung: **24 Blöcke, 768 bewertete Varianten, ausschließlich development**. Am Ende des vollständigen Laufs steht `status: complete` mit 24 abgeschlossenen Blöcken. Ein schlechter Score ist ein gültiges Ergebnis und kein Ausführungsfehler.

Verwendet wird der bereits eingesetzte Checkpoint `unsloth/gemma-2-2b` bei Commit `25319945f7fd83b8b903e12081777b7eef2ba993`, BF16, Batchgröße 1. Kein Modellwechsel, keine automatische Ausweichroute, kein SAE-Eingriff und keine freie Textgenerierung in diesem Lauf.

## 2. Genau dieses Archiv zurückgeben

Der Export enthält `report.md`, `analysis.json`, drei Abbildungsformate, den vollständigen Aufgabenplan, die originalen Harness-Ergebnisse einschließlich Prompts/Antwortwahrscheinlichkeiten, Quellstand, Umgebung und Prüfsummen.

Nach dem Export:

```bash
git add -f exports/harness-baseline-v1.tar.gz
git commit -m "Add standard-harness development baseline v1"
git push origin main
```

Danach hier melden: **„harness-baseline-v1 ist gepusht“**. Neue Laufordner sind standardmäßig ignoriert; `git add -f` nimmt bewusst nur das Ergebnisarchiv auf. Die bereits eingecheckten historischen Läufe bleiben erhalten. Kein `git add .` nötig.

## Pause oder Fehler

- Der Lauf hat ein kooperatives Zeitlimit von einer Stunde. Ein laufender Szenarioblock darf noch fertig werden. Bei `paused` oder `interrupted` denselben **run-Befehl** erneut ausführen; vollständig gespeicherte Blöcke werden geprüft und übersprungen.
- Optional zuerst nur einen Block prüfen: denselben run-Befehl mit `--max-blocks 1` ausführen; anschließend ohne diesen Zusatz fortsetzen. Das verändert weder den Datensatz noch die Auswertung.
- Bei `failed`: Fehlermeldung behalten. Der Lauf speichert `error.json` und versucht fehlgeschlagene Blöcke nicht automatisch erneut. Das unvollständige Ergebnis kann mit dem export-Befehl oben ebenfalls zurückgegeben werden. Keine Paket-/Promptänderungen im bestehenden Laufordner.
- Falls das Zielarchiv schon existiert, einen neuen Archivnamen verwenden. Keine Ergebnisse überschreiben.
- Falls Git wegen lokaler Änderungen nicht aktualisieren kann, die Meldung weitergeben; keine lokalen Änderungen wegsetzen oder verwerfen.

## Festgelegtes Messverfahren

- Drei Familien: Handlungszuordnung, Informationszugang, Fähigkeitsänderung.
- Pro Familie Entwicklungsszenarien 0–7; alle 32 Rollen-, Fakten-, Perspektiv- und Antwortpositionsvarianten bleiben zusammen. Das sind **acht Szenarien pro Familie**, nicht 256 unabhängige Beobachtungen.
- Vier feste Lösungsbeispiele pro Familie aus Entwicklungsszenarien 36–39. Diese Episoden werden nicht bewertet; Beispiele sind über A/B/C/D, Selbst/Fremd und zugewiesene Identität ausgeglichen.
- Ein Promptformat, vier Beispiele, Fortsetzungen ` A`, ` B`, ` C`, ` D`. Das Harness bewertet die vollständige jeweilige Fortsetzung. Es gibt keine Suche nach dem besten Antwortformat.
- Vor jeder Auswertung wird die Kontextlänge geprüft; überlange Prompts lösen einen Fehler aus und werden nicht still gekürzt.
- Der Bericht zeigt Gesamt- und Untergruppenrichtigkeit sowie gekoppelte Faktenwechsel. Eine bestandene 80-%-Entwicklungsprüfung ist **keine** bestätigende Analyse und öffnet den Testsatz nicht.

Das ist ein revidiertes Messprotokoll. Gegenüber dem bisherigen Lauf ändern sich sowohl Scoring als auch die vier Lösungsbeispiele. Eine mögliche Verbesserung kann deshalb nicht allein dem Leerzeichen zugeschrieben werden. Wenn diese feste Baseline scheitert, dokumentieren wir den Pilotbefund. Wenn sie besteht, folgt zuerst der Vergleich mit dem unveränderten Interventionspfad und danach ein eigenes Validierungsprotokoll. Der bisherige 350.000-Versuche-Sweep startet in keinem Fall automatisch.

Die neue GPU-Runde ist lokal noch nicht ausgeführt. CPU-Integrationstests prüfen die Software, nicht Gemmas Aufgabenfähigkeit. Für genau dieses Vier-Beispiele-Verfahren liegt noch keine gemessene GPU-Laufzeit vor.
