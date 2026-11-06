# Quellen, Theorie & Projekt-Kontext: „Die Ich-Illusion ist ein Vektor“

Dieses Dokument bündelt die theoretischen Grundlagen, Primärquellen und den experimentellen Aufbau für das Essay- und Mechanistic-Interpretability-Projekt **„Die Ich-Illusion ist ein Vektor“**.

---

## 1. Externe Primärquellen & Frameworks

### Mechanistic Interpretability & Transformer-Architektur
* **Anthropic Foundation Paper (Elhage et al., 2021):**  
  [*A Mathematical Framework for Transformer Circuits*](https://transformer-circuits.pub/2021/framework/index.html)  
  *Kernaussage:* Einführung des **Residual Streams** als zentraler linearer Kommunikationskanal (Datenbus), in den Attention-Heads und MLPs additiv lesen und schreiben.
* **Superposition & Sparse Autoencoders (Elhage et al., 2022 / Bricken et al., 2023):**  
  [*Toy Models of Superposition*](https://transformer-circuits.pub/2022/toy_model/index.html) & [*Towards Monosemanticity: Decomposing Language Models With Dictionary Learning*](https://transformer-circuits.pub/2023/monosemantic-features/index.html)  
  *Kernaussage:* Sprachmodelle komprimieren mehr Konzepte als verfügbare Dimensionen ($d_{\text{model}}$) durch fast-orthogonale Überlagerung (*Superposition*). Sparse Autoencoders (SAEs) entflechten diese Überlagerung wieder in monosemantische Richtungen.
* **Gemma Scope (Lieberum et al., Google DeepMind, 2024):**  
  [*Gemma Scope: Open Sparse Autoencoders Everywhere All At Once on Gemma 2*](https://arxiv.org/abs/2408.05147)  
  *Artefakt im Projekt:* `gemma-scope-2b-pt-res-canonical` (`layer_14/width_16k/canonical`, JumpReLU-SAE mit $16.384$ Features auf $d_{\text{model}} = 2304$).
* **Representation Engineering & Activation Steering (Zou et al., 2023 / Turner et al., 2023):**  
  [*Representation Engineering: A Top-Down Approach to AI Transparency*](https://arxiv.org/abs/2310.01405) & [*Activation Addition: Steering Language Models Without Optimization*](https://arxiv.org/abs/2308.10248)  
  *Kernaussage:* Hochstufige Konzepte (Metakognition, Selbstbezug, Täuschung) lassen sich über Kontrast-Paare als lineare Richtungsvektoren isolieren und zur Laufzeit kausal in den Residual Stream injizieren.

### Software-Frameworks (im Conda-Env `mechinterp`)
* **TransformerLens (Neel Nanda et al.):**  
  [https://github.com/TransformerLensOrg/TransformerLens](https://github.com/TransformerLensOrg/TransformerLens) — Python-Framework zum Auslesen (`run_with_cache`) und Manipulieren (`add_hook`) interner Aktivierungen.
* **SAELens (Joseph Bloom et al.):**  
  [https://github.com/jbloomAus/SAELens](https://github.com/jbloomAus/SAELens) — Framework zum Laden und Analysieren von Sparse Autoencodern (Gemma Scope).

---

## 2. Philosophischer Rahmen: Illusionismus (Dennett & Frankish)

* **Daniel C. Dennett (1991):** *Consciousness Explained* — Kritik am **Kartesischen Theater**: Es existiert kein zentraler innerer Beobachter im Gehirn, dem Erlebnisse auf einer inneren Bühne vorgeführt werden. Stattdessen wirken verteilte, parallele Entwürfe (*Multiple Drafts Model*).
* **Keith Frankish (2016):** [*Illusionism as a Theory of Consciousness*](https://philpapers.org/rec/FRAIAA-4) (*Journal of Consciousness Studies*) — Unterscheidung zwischen physischen/funktionalen Gehirnzuständen (*Quasi-Phänomenalität*) und der vermeintlich nicht-physischen, unaussprechlichen Erlebnisqualität (*Qualia*).
* **Der kognitive Fehlbericht (Cognitive Misreport):**  
  Ein komplexes System hat keinen direkten introspektiven Zugriff auf seine Milliarden Einzelgewichte oder Feuerungsraten. Um sich selbst zu regeln (Allostase, Fehlerkorrektur, Handlungsplanung), baut es ein stark komprimiertes **User-Interface** (ein vereinfachtes Selbstmodell). Wenn dieses Interface über seine eigenen Zustände berichtet, verwechselt es die Kompressions-Abkürzung mit einer metaphysischen Substanz („Ich“, „Bewusstsein“).

---

## 3. Technische & Empirische Beweisführung in diesem Repo

Unsere Experimente auf **Gemma 2 2B** (`torch.bfloat16`, Schicht 14 `blocks.14.hook_resid_post`) liefern die direkte mechanistische Übersetzung von Dennetts und Frankishs These:

| Experiment | Skript / Ort | Mechanismus | Beobachteter Effekt | Philosophische Bedeutung |
| :--- | :--- | :--- | :--- | :--- |
| **1. Dichter Metakognitions-Vektor** | `gemma_steering.py` | Mean-Difference $\vec{v}_{\text{metacog}} \in \mathbb{R}^{2304}$ zwischen introspektiven und neutralen Prompts, injiziert an Layer 14 ($\alpha = +180$). | Modell wechselt von nüchterner Fachsprache zu: *„...the ability to understand what I am and why I have a perspective on what is, from my understanding as I reflect upon what is through my own self-awareness.“* | Im komprimierten 2304-D-Raum entsteht durch **Superposition** der Eindruck eines geschlossenen, reflektierenden „Ichs“. |
| **2. SAE Feature `#2728` (Self-Monitoring)** | `sae_steering.py` | Isolierte Decoder-Richtung $W_{\text{dec}}[2728]$ aus dem 16k Gemma Scope SAE ($\Delta = +7.17$, Neutral $= 0.0$). Top-Logits: `[' self', 'self', ' Self', ..., ' introspection']`. | Modell definiert Intelligenz funktional: *„...the ability to monitor its behaviour and that of others with a high degree of confidence, from which one can then reflect upon what has just happened and work out how to improve.“* | **Der nackte Regelkreis:** Funktionale Selbstüberwachung und Fehlerkorrektur kommen komplett ohne ein subjektives „Ich“ aus. |
| **3. SAE Feature `#10230` (First-Person Agency)** | `sae_steering.py` | Isolierte Decoder-Richtung $W_{\text{dec}}[10230]$ ($\Delta = +9.49$, Neutral $= 0.0$). Top-Logits: `[' my', ' I', 'my', ' myself']`. | Modell wechselt in eine persönliche Anekdote: *„I was recently asked by a colleague... it would be helpful to share my experiences with me...“* | **Die rhetorische Fassade:** Das grammatische „Ich“ ist ein separates Oberflächen-Feature ohne eigene metakognitive Tiefe. |

### Die Kernthese des Essays („Die Ich-Illusion ist ein Vektor“)
Was uns als unteilbares, rätselhaftes „Ich-Bewusstsein“ erscheint, ist im neuronalen Netz kein metaphysisches Phänomen, sondern die gleichzeitige Aktivierung zweier orthogonaler Schaltkreise im Residual Stream: eines **funktionalen Kontroll- und Monitoring-Vektors (`#2728`)** und einer **sprachlichen Erste-Person-Fassade (`#10230`)**.
