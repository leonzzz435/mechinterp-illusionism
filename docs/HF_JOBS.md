# Next job: Qwen pilot

The historical Gemma job below is complete. For the newly implemented, separately budgeted
Qwen protocol use [the Qwen handover](QWEN_PILOT.md), explicit
`--config configs/qwen-pilot.json`, and `.hf-jobs/qwen-pilot.json` for its receipt.
The first-job authorization does not cover a new submission.

---

# Gemma-Baseline auf Hugging Face Jobs

**Aktueller Ausführungsweg: ein Cloud-Job für das bestehende Experiment.** Modell, Checkpoint, vier Beispiele, 768 Entwicklungsvarianten und Auswertung bleiben bei `configs/harness-baseline.json`. DeepSeek, weitere Modelle und große Sweeps gehören nicht zu diesem Schritt.

**Erster Lauf abgeschlossen:** [Ergebnis und Prüfung](HF_PILOT.md). Alle 768 Varianten wurden ausgewertet; alle drei Fähigkeitsprüfungen scheiterten. Der erste freigegebene Job ist damit beendet. Die Startbefehle unten dokumentieren den Ablauf und sind kein Auftrag für einen zweiten Lauf. Login und privater Ergebnisspeicher unter `zett13` funktionieren bereits.

## Einmalig vom Nutzer benötigt

1. Hugging-Face-Nutzername oder gewünschte Organisation.
2. Ein HF-Konto mit positivem Compute-Guthaben. Ein PRO-Abo ist laut aktueller Jobs-Dokumentation keine Voraussetzung; Prepaid-Guthaben genügt.
3. Lokale Anmeldung mit einem Token, der Jobs starten/verwalten sowie das private Dataset-Repository `NAMESPACE/mechinterp-illusionism-results` erstellen und beschreiben darf. Den Token nur im lokalen Login eingeben:

```bash
uvx --from 'huggingface-hub[cli]==0.36.2' hf auth login
```

Für den ersten Lauf wurden im Gespräch **maximal 10 US-Dollar** freigegeben. Das erlaubt einen Job; weitere Jobs starten nicht automatisch. Es werden keine Credits automatisch gekauft oder Abonnements abgeschlossen.

## Vorbereiten und einmal starten

`NAMESPACE` in den folgenden Befehlen durch den tatsächlichen HF-Namen ersetzen. Die Startdatei nutzt eine eigene kleine uv-Umgebung; auf dem Privatrechner werden dafür weder CUDA-Pakete noch Modellgewichte installiert.

```bash
git pull --ff-only origin main
uv run --script scripts/hf_jobs.py plan --namespace NAMESPACE --budget-usd 10
uv run --script scripts/hf_jobs.py submit --namespace NAMESPACE --budget-usd 10
```

`plan` liest nur den aktuellen Hardwarepreis und den Git-Stand. `submit` prüft Anmeldung, veröffentlichten Commit und privaten Ergebnisspeicher, legt bei Bedarf das private Dataset-Repository an und startet genau einen Job. Ein unsauberer Git-Stand oder ein bereits vorhandener Startbeleg verhindert den Start.

Das GitHub-Repository ist privat. Deshalb lädt der Starter die eingecheckten Git-Objekte als Bundle in das ebenfalls private HF-Repository. Der Job lädt dieses Bundle von einem fixierten HF-Commit, prüft dessen SHA-256 und checkt den ausgewählten Git-Commit aus. Unversionierte lokale Dateien und Git-Zugangsdaten sind nicht enthalten. Ein GitHub-Token im Cloud-Job ist nicht erforderlich.

Festgelegt sind:

- **Eine NVIDIA L4 mit 24 GB**, Flavor `l4x1`.
- **Zwei Stunden hartes Provider-Zeitlimit**, einschließlich Installation und Downloads. Der eigentliche Harness-Lauf behält sein kooperatives Ein-Stunden-Limit.
- Image `ghcr.io/astral-sh/uv:0.9.7-python3.11-bookworm`, per SHA-256-Digest fixiert. Der genaue Git-Commit wird ausgecheckt; `uv sync --locked --no-dev --extra gpu --extra eval` installiert die vorhandene Umgebung.
- Vor jeder Einreichung aktueller Preis von `https://huggingface.co/api/jobs/hardware`. Bei 0,013333 USD pro Minute beträgt die konservative Compute-Obergrenze inklusive einer Rundungsminute **1,613293 USD**. Der Start wird abgelehnt, wenn die errechnete Compute-Obergrenze mehr als die Hälfte des expliziten Budgets beansprucht. Das ist kein kontoweites Abrechnungslimit; Steuern und gegebenenfalls bestehende Speicher-/Kontogebühren sind davon getrennt.
- Zugangsdaten gehen ausschließlich über HF Jobs `secrets`, nicht in Konfigurationen, Startbelege oder Git.

Die vorhandene CUDA-Umgebung lief im ersten Job erfolgreich auf einer L4. Bei künftigen Ausführungsfehlern erfolgt keine automatische Änderung von Paketen, Modell oder Hardware.

## Status, Logs und Ergebnisse

Der lokale Startbeleg `.hf-jobs/first.json` enthält Job-ID, URL, Commit, Hardwarepreis, Budget und Ergebnisort. Er ist git-ignoriert und enthält keinen Token.

```bash
uv run --script scripts/hf_jobs.py status
uv run --script scripts/hf_jobs.py logs
uv run --script scripts/hf_jobs.py fetch
```

Die Daten liegen anschließend unter `.hf-jobs/downloads/RUN_NAME/`:

- `run/report.md`, `run/analysis.json`, `run/figures/`: Bericht und SVG/PDF/PNG.
- `run/blocks/`, `run/tasks/`, `run/plan.json`, `run/source/`: rohe Harness-Ausgaben, Aufgaben und Quellstand.
- `job.json`: GPU-/Job-Daten, Git-Commit und Image.
- `exports/RUN_NAME.tar.gz` und `export.json`: vollständiges Archiv und seine Prüfsumme.

`fetch` lädt genau einen Commit des Ergebnis-Repositories und prüft vorhandene Export-Prüfsummen. Ein früher Zwischenstand hat noch kein Exportarchiv; `export_verified: false` bleibt dann sichtbar. Das private HF-Repository ist der Datentransport. Ergebnisse müssen nicht mehr auf dem Arbeitsrechner manuell in Git eingecheckt werden.

## Abbruch und Teilstände

```bash
uv run --script scripts/hf_jobs.py cancel
```

Das Beenden der lokalen Log-Anzeige stoppt den entfernten Job nicht; dafür dient `cancel` oder das Provider-Zeitlimit.

Nach jedem vollständig gespeicherten 32-Varianten-Block werden Daten und Manifest synchron in das private Dataset-Repository geladen. Das Modell bleibt zwischen den Blöcken geladen. Ein harter Abbruch kann den gerade laufenden oder noch nicht übertragenen Block verlieren; vorherige bestätigte Uploads bleiben erhalten. Bei einem gewöhnlichen Fehler werden auch der Fehlerzustand und ein Teilbericht exportiert.

Ein unterbrochener Job wird nicht automatisch neu gestartet. Zuerst Ergebnisse und Logs holen und prüfen; der vorhandene Harness kann unveränderte, vollständig heruntergeladene Zwischenstände fortsetzen. Ein weiterer Cloud-Job mit Wiederherstellung ist ein gesonderter Arbeitsauftrag, kein eingebauter Neustart-Loop.

Wenn die Startantwort verloren geht, bleibt `submission_unknown` im Beleg stehen. Nicht erneut einreichen und den Beleg nicht löschen: auf der HF-Jobs-Seite prüfen, ob der Job bereits läuft. Dasselbe gilt für ein `submitting`, falls der lokale Prozess direkt nach der Anfrage beendet wurde.

## Wissenschaftlicher Status

Ein erfolgreicher Cloud-Lauf ist weiterhin nur die festgelegte Entwicklungs-Baseline. Er öffnet keine Validierungs-/Testdaten und startet keine Interventionen. Ein Vergleich mit Blackwell wäre ein gesonderter Vergleich desselben Messprotokolls; die alten Null-Beispiel-Ergebnisse sind dafür keine numerische Referenz.

Quellen: [Jobs-Konfiguration und Secrets](https://huggingface.co/docs/hub/en/jobs-configuration), [Preise und Guthaben](https://huggingface.co/docs/hub/en/jobs-pricing), [Jobs-Quickstart](https://huggingface.co/docs/hub/en/jobs-quickstart). Die Einreichung nutzt die lokal geprüfte API von `huggingface_hub==0.36.2`; aktuelle SDK-Funktionen wie Volume-Mounts werden nicht vorausgesetzt.
