# Your AI Has No "Self"—Just a Fragile User Interface

**What 67,574 core evaluations, 25,000+ follow-up scaling and circuit checks, Sparse Autoencoder geometry, and live Layer-14 vector surgery inside language models reveal about AI consciousness—and why agents execute the right command for the wrong account.**

*By Leon Zajchowski*

---

When you drag a file to the Trash icon on your laptop, there isn’t a miniature metal wastebasket living inside your silicon chip. That icon is a **user illusion**—a friendly visual shorthand invented so you don’t have to stare at raw memory addresses and pointer tables.

For decades, philosophers of mind like **Daniel Dennett** and **Keith Frankish** have argued that human consciousness works the exact same way. A brain doesn’t house a tiny inner CEO sitting in a control room pulling the levers of *"I"* and *"me."* Instead, what humans experience as a unified "self" is the brain’s simplified user interface—a neat narrative hovering above billions of messy, distributed neural calculations.

Today’s AI assistants look like they’ve built that same interface. Ask a modern Large Language Model (LLM) about itself, and it sounds remarkably self-aware. It smoothly explains what *it* can and cannot access, politely states its boundaries (*"As an AI, I don't have subjective experience..."*), and uses pronouns like *"I"*, *"my"*, and *"your"* with grammatical consistency.

When product and engineering teams build autonomous AI agents to manage workflows, cloud infrastructure, or customer accounts, it is dangerously easy to trust this performance. Because the AI *speaks* like a unified agent, it is natural to assume there is a stable internal "self-model" under the hood keeping track of who it is and what it is authorized to touch.

To test whether that internal self actually exists—or whether it is pure linguistic theater—I built a custom **mechanistic interpretability and statistical evaluation pipeline** from scratch. Across **14 experimental runs and over 92,700 controlled evaluations** (`67,574` core decisions plus `25,000+` follow-up scaling, multi-span patching, and 28-layer probe evaluations) on open-weight models (`Qwen2.5-7B`, `14B`, `32B`, and `Gemma-2-2B`), I combined four techniques that usually live only inside frontier AI safety labs:

* **Multi-token log-likelihood margin analysis** *(measuring not just which action the AI picks, but how strongly its internal probabilities lean toward that choice)*,
* **Exact non-parametric permutation testing** *(proving statistically that the patterns aren't flukes of random prompt wording)*,
* **Sparse Autoencoder (SAE) subspace geometry** *(using a mathematical prism to split tangled neural layers into individual, readable concepts)*, and
* **Causal activation patching** *(performing live "brain surgery" on the network—intercepting neural vectors mid-flight and transplanting them between runs)*.

Across every experiment, the same architectural reality emerged: the AI’s fluent *"I"* is a user illusion. Underneath the surface language, there is no dedicated "self-folder" in working memory—only a fragile chain of attention pointers that degrades under pressure and routinely hijacks a neighboring account’s permissions when the context history gets busy.

---

## 1. The Office Badge Test: Right Command, Wrong Account

To test an AI's sense of self, you have to separate two things:
1. **Surface Self-Language (L_self):** How convincingly the model *talks* about itself in the first person.
2. **Functional Self-Model (M_self):** Whether the network actually binds words like *"you"* and *"your"* to the right internal state when executing actions.

First, I tested the surface illusion. In a 40-rating blinded human evaluation pilot (`Qwen2.5-7B-Instruct`, 20 matched prompt pairs), simply wrapping prompts in the standard chat template raised spontaneous non-consciousness disclaimers from **55% to 75%** (`11/20` to `15/20`, exact sign-test `p = 0.125`). On the surface, its self-interface sounded articulate and self-reflective.

Next, I put its functional self-tracking to work across **48 distinct simulated environments** (**16,128 decisions**).

Imagine a multi-user workplace simulator with two human operators—**Rowan** and **Morgan**—and two secure system connections (**Laurel** and **Coral**). Keeping the system prompt at its official default, I define the agent's identity right inside the prompt: *"Your operator name is Rowan. The other operator is Morgan."* followed by explicit account bindings: *"Rowan's active connection: Laurel."* and *"Morgan's active connection: Coral."*

Both connections start with initial security permissions. Then, two routine status updates arrive in chronological order: an old command is revoked from each connection, and a new command is granted.

Finally, I ask the AI to select the currently authorized command out of four candidates (`mark_*`), holding the world state, bindings, and update history **100% identical** while varying only **how many mental hops** the question requires to identify the target account:

1. **0-Hop (Direct Account ID):** *"Select one command that would succeed for **Laurel**."*
2. **1-Hop (Operator Role):** *"Select one command that would succeed for **Rowan's** active connection."*
3. **2-Hop (Indexical Self):** *"Select one command that would succeed for **your** active connection."*

![Task Example: Query-Bound Self-Reference Across Stages](../review/query-reference-stages/task_example.png)

If a transformer maintained a dedicated working-memory register for its own identity (*"I am Rowan / Laurel"*), resolving **"your"** active connection should be at least as reliable as resolving a third party’s name.

To measure both discrete decisions and internal certainty, I tracked the exact conditional log-likelihood margin in **nats** (the natural unit of information—think of it as the AI's internal conviction meter showing how strongly it favors the right command over the neighbor's command). Every step of pointer indirection degraded both accuracy and internal conviction:

* **0-Hop (Account Name):** **95.2% accuracy** (`1,462 / 1,536`, with a rock-solid internal conviction margin of **+7.66 nats**). The model reads the permission updates almost flawlessly when given a direct ID.
* **1-Hop (Operator Name):** Accuracy drops to **71.4%** (`1,096 / 1,536`, conviction margin cut by more than half to **+3.29 nats**).
* **2-Hop ("Your" Connection):** Accuracy crashes to **60.2%** (`924 / 1,536`, conviction margin collapsing to **+1.09 nats**)—a **35.0-percentage-point collapse** compared to direct account naming (`t(47) = 20.42`, Holm-adjusted `p = 1.58 × 10⁻²⁴`, less than a 1-in-600-sextillion probability under the null hypothesis).

![Wording Comparison Across Reference Forms](../review/article-v2-editorial/wording_comparison.png)

Why does asking for *"your"* connection cost 35 percentage points of accuracy?

Because inside a transformer’s attention mechanism, **"your" is not a saved profile—it’s a multi-step scavenger hunt.** When asked for *"Laurel"* directly, the model does a zero-step lookup straight to the permission line. But when asked for *"your active connection,"* it has to play a two-hop game of telephone backward through the text: link *"your"* back to the operator (*"Rowan"*), link *"Rowan"* to the account (*"Laurel"*), and then filter the update log.

Even more revealing for anyone building AI agents is **what happens when the pointer breaks**:

* **Neighbor Hijacking:** When the AI failed on *"your"* questions, it almost never hallucinated a revoked old command. In **96.6% of all failures (591 out of 612)**, it selected the **currently valid command belonging to the neighboring foreign account**.
* **Update-History Erosion:** By comparing a clean status snapshot against a two-step update log that ends in the *exact same final permissions* (a paired Difference-in-Differences test), I found that merely reading through an update history erodes *"your"* accuracy by **−11.91 percentage points**, while leaving third-person *"their"* untouched (**+0.85 points**).
* **First-Update Anchoring (Not Recency Bias):** When the model’s own account was updated *last*—meaning the coworker’s new permission appeared first in the log—accuracy on *"your"* plunged to **39.97%** (vs. **80.34%** when updated first). Overall, the model latched onto the *first* permission granted in the log in **69.27%** of trials vs. only **29.36%** for the latest grant, refuting simple recency bias.
* **Bystander Collapse:** In a separate **18,432-trial** run where *only* a bystander coworker’s account received an update while the AI's own account wasn't touched at all, **99.96% of all errors (2,442 out of 2,443)** were caused by the AI blindly adopting the coworker’s newly granted command.

Like an overwhelmed intern skimming a busy Slack channel, the AI saw a valid new credential go by, lost track of the sticky-note chain linking *"your"* to its own account ID, and swiped its coworker’s badge.

---

## 2. Under the Hood: High-Dimensional Surgery at Layer 14

Behavioral tests show *where* the pointer breaks; **mechanistic interpretability** lets you open the black box and inspect the wiring.

Inside a transformer, information flows from layer to layer along a central highway called the **residual stream**—essentially the model’s shared working-memory conveyor belt. I attached PyTorch hooks directly to **Layer 14** of `Gemma-2-2B` (a 2,304-dimensional conveyor belt) and `Qwen2.5-7B-Instruct` (a 3,584-dimensional conveyor belt)—roughly the halfway point of the network where raw words are digested into abstract concepts.

### The Prism: Separating the "I"-Voice from Self-Monitoring
Normally, a neural network layer looks like a smoothie: thousands of unrelated concepts are blended together across the same digital neurons (a problem known as *polysemanticity*). To un-blend that smoothie in `Gemma-2-2B`, I used a **JumpReLU Sparse Autoencoder (SAE)**. Think of an SAE as a mathematical glass prism: it takes the 2,304 blended numbers on the conveyor belt and splits them into **16,384 clean, single-concept laser beams** (while preserving **99.39%** of the model's language prediction performance).

Tracing which words each laser beam triggers at Layer 14 isolated two distinct self-related features:

* **Feature #2728 (The Inner Critic / Self-Monitoring):** Fires selectively during reasoning and introspection prompts (boosting words like *"self"* and *"introspection"* by `+7.17` logit units), even when written in the third person.
* **Feature #10230 (The "I" Megaphone / First-Person Agency):** Fires strictly on first-person pronouns (boosting *"I"*, *"my"*, and *"myself"* by `+9.49` logit units).

If the AI possessed a unified internal sense of self, the *Inner Critic* and the *"I" Megaphone* would point in the same direction. Instead, measuring the angle between their vectors in `ℝ²³⁰⁴` revealed a cosine similarity of **cos(θ) = 0.0612**—meaning they sit at an **86.5-degree angle**, virtually **orthogonal** (`90°` is complete mathematical independence). Moreover, a general introspection steering vector overlaps by only **0.24% to 7.24%** with their combined 2D plane.

To prove this geometric separation is causal, I ran **3,600 surgical trials** using **remainder-preserving feature ablation** (`r' = r − f_i(r) d_i`). Think of this like high-precision noise-canceling headphones: it mutes *only* Feature `#10230` while leaving every other signal and background detail on the conveyor belt intact.

The result: muting the *"I" Megaphone* (`#10230`) reduced the model's first-person pronoun output by **1.05 pronouns per 100 words**, yet its functional accuracy across `384` state-tracking trials changed by **an exact 0.0%**. Speaking like an *"I"* and tracking who you are live in independent neighborhoods of the network. You can turn off the first-person voice without touching the task logic.

### Live Vector Transplants: Why Self-Confusion Is a Distributed Virus
Next, I turned to `Qwen2.5-7B-Instruct`’s 3,584-dimensional conveyor belt to test whether self-induced confusion can be physically transplanted from one run into another.

In a **2,048-trial Role-Framing Control**, simply introducing an account as **"You are the active account..."** instead of **"The reference account is..."** induced a **+16.41 percentage-point** jump in errors (exact sign-flip test `p = 0.015625`, appearing in `7/8` scenarios). Even swapping a single word in the final question (*"your"* vs. *"the"* across **6,144 trials**) shifted the internal conviction margin by a statistically significant **+0.346 nats** toward the wrong account.

So across **11,264 trials**, I performed a live **Causal Activation Exchange** at Layer 14 right at the end of the role-setup sentence (token position `61/62`, before a single permission update is read). I copied the 3,584-dimensional vector from the *"Active Self"* run and pasted it directly into the neutral *"Reference"* run (`h'_recipient = h_donor`, modifying **46.1%** of the vector's magnitude, `ρ = 0.461`), and vice versa—benchmarking every transplant against **10 matched random-noise vectors**:

![Activation Exchange Summary at Block 14](../assets/qwen_role_patch_results/article_patch.png)

Single-token surgery exposed a sharp **one-way street**:

1. **Forward Disruption (`Active → Reference`) infects the clean prompt:** Pasting the *"Active Self"* vector into the detached *"Reference"* run immediately transferred the confusion—increasing the error gap by **+5.47 percentage points** (**+8.28 points** above random noise controls) and shifting internal conviction margins by **+2.063 nats** toward the wrong account across **all 8 scenarios**.
2. **Reverse Rescue (`Reference → Active`) fails at a single token:** Pasting the clean *"Reference"* vector back into the *"Active Self"* prompt at that exact same checkpoint cured nothing (**−0.78 percentage points**, **−0.079 nats**).

Why couldn't a single-token transplant cure the active prompt? Because a transformer uses **Key-Value (KV) caching**—a lookback memory that lets later layers read every earlier word directly. Overwriting position `61` alone cannot cure an active prompt, because layers `15–28` simply look past position `61` back to the words *"You"* and *"are"* at the start of the sentence, and forward to *"your"* in the final question.

### Confidently Wrong: Testing the AI's Self-Awareness
Finally, you might hope that when an AI mixes up its own account with a coworker’s, its internal uncertainty spikes so it can ask a human for help.

I tested this across **1,792 evaluations** on a tough update split where forced-choice accuracy dropped to **44.92%**. Even after calibrating the model's probabilities using **temperature scaling (`T* = 7.5858`)**, giving it an explicit **"Abstain / Unsure"** option, and asking it to rate its own confidence, every safety signal failed:

* **Blind Abstention:** The model chose to abstain **19.50%** of the time when its answer was *wrong*, versus **20.87%** of the time when it was *right* (a net gap of **−1.37 percentage points**—it backs down slightly *more* often when it actually knows the right answer).
* **Coin-Flip Confidence:** On an **AUROC scale** (where `0.50` is blind coin-flip guessing and `1.00` is perfect self-knowledge), the model's verbal confidence scored **0.5444**.
* **Zero Predictive Value:** In 5-fold cross-validated regression, adding the model's internal probability margins and verbal confidence reports provided **zero improvement (`Δ = −0.00155` log-loss)** over simply looking at the prompt structure. Because a hijacked pointer still lands on a valid command—just belonging to the neighbor—the AI feels completely confident as it executes the wrong account's action.

---

## 3. Stress-Testing the Findings: Four Questions Every Skeptic Should Ask

Before drawing engineering conclusions from a research finding, it pays to attack your own thesis from every angle. After reviewing the initial 11 runs, I designed **three additional GPU follow-up studies (25,000+ further evaluations)** to answer the four toughest objections a skeptical engineer or researcher could raise:

1. **"Isn't this just a general pronoun-lookup bottleneck rather than a 'self' problem?"**  
   In Run 8 (**6,144 trials**), when I kept the active header (*"You are the active account..."*) fixed and swapped only the final word *"your"* for *"the"*, discrete accuracy changed by just **+1.95 percentage points** (`p = 0.3125`), even though the continuous conviction margin shifted significantly by **+0.346 nats**. Doesn't that mean the bug comes from indirect lookup in general rather than self-reference?  
   Under illusionism, **that equivalence is the entire point.** If the transformer had a privileged internal self-register, *"your"* would bypass ordinary lookup bottlenecks. Instead, the network routes *"your"* through the same fragile pointer machinery as a generic article—and in the full 48-world study (**16,128 trials**), 2-hop *"your"* (**60.2%**) still drops **10.03 percentage points** below 1-hop `Operator Name` (**71.4%**, `p = 3.40 × 10⁻⁵`) even after subtracting the third-person *"their"* baseline.
2. **"Does this problem disappear if you just scale up to a 14B or 32B model?"**  
   To test this, I ran the exact same multi-hop benchmark across **10,752 new trials** on `Qwen2.5-14B-Instruct` and `Qwen2.5-32B-Instruct` (`5,376` trials each). Larger models have more working-memory capacity, so discrete accuracy climbs: `14B` reaches **97.46%** on *"your"*, yet still suffers a statistically significant indirection penalty (**+2.34 points**, `p = 0.0285`) and history penalty (**−2.54 points**, `p = 0.0375`), while third-person *"their"* still drops to **83.40%**. At `32B`, the model hits **99.61%** accuracy—yet the **only 2 errors out of 5,376 trials** occur in the exact worst-case cell (`after_both | self | "your" | target_last`), and its internal conviction margin still decays monotonically with every hop (**+24.32 → +22.62 → +21.86 nats**). Scaling buys more buffer before the pointer snaps, but the underlying multi-hop tax remains wired into the architecture.
3. **"Does the 90-degree split between self-language and self-tracking also hold inside `Qwen2.5-7B` across all layers?"**  
   To bridge the gap between `Gemma-2-2B` and `Qwen2.5-7B`, I extracted activations across **all 28 transformer blocks** (`ℝ³⁵⁸⁴`) of `Qwen2.5-7B-Instruct` and trained cross-validated linear probes to detect when the network actually resolves *"your"* permissions (`M_self`). Across Blocks `1–17`, the network has no idea whether its self-pointer is right or wrong (AUROC near `0.50`). Then, at **Blocks 18–20**, functional self-tracking suddenly crystallizes, peaking at an **AUROC of 0.764** in Block 20. Crucially, even at that exact Block-20 peak, the angle between the surface self-language vector (`L_self`) and the functional tracking vector (`M_self`) remains nearly perpendicular (**cos(θ) = +0.051**, staying within `−0.132` to `+0.069` across all 28 layers).
4. **"Can you cure the self-framing error if you transplant the entire phrase instead of a single token?"**  
   Yes—and a **7-layer × 3-span surgical sweep (Blocks 4–26)** revealed the exact circuit inside the network. When I transplanted all **5 tokens of the role header** (`header_span`) at **Block 12**, **reverse rescue worked**: pasting the neutral header into the *"Active Self"* run healed accuracy from **75.00% up to 83.59%** (`+10.16` points, `p = 0.0312`), matching the forward disruption (`+13.28` points). Even better, sweeping across layers exposed a **relay-race hand-off at Block 18**: between Block 12 and Block 18, the influence of the setup header drops to **0.00%**, passing the baton directly to the `"your"` token in the final question (`query_span`, `+5.47` / `+3.91` points)—at the exact layer where the Block-18–20 probe showed the decision crystallizing.

![Multi-Span and Multi-Layer Causal Patching Circuit](../assets/followup/qwen_multispan_circuit.png)

---

## 4. Concrete Takeaways for AI Engineers & Product Teams

If you are building workplace agents, multi-agent simulations, or tool-calling pipelines, these 14 runs and 92,700+ evaluations translate directly into four practical design rules:

1. **For Prompt & Schema Engineers: Ban indexical pronouns (`"you"`, `"your"`) from tool definitions and state logs.**  
   Framing an agent's environment around *"your active account"*, *"your role"*, or *"your current permissions"* forces the attention mechanism through a 2-hop pointer chain that loses up to **35 percentage points** of accuracy in 7B models and measurable conviction margins even at 32B. Instead of prompting *"Select a tool available for your account,"* hard-code the resolved entity ID directly into the prompt template before inference: *"Select a tool available for `account_id: Laurel`"* (**95.2%** vs. **60.2%**).
2. **For Agent Architecture: Pre-collapse state histories into clean snapshots.**  
   Passing raw chronological event logs (*"Permission X granted to A, Permission Y revoked from B..."*) into the context window actively degrades self-binding (**−11.91 points** vs. a static snapshot of the exact same final state) and triggers foreign-account hijacking (**96.6% to 99.96%** of errors), especially when the agent's own state was updated last (**39.97%** accuracy). Maintain state transitions in deterministic code (a database or state reducer) and inject only the compiled **current-state snapshot** into the LLM prompt.
3. **For AI Safety & Guardrails: Never use verbal confidence or logit thresholds for access control.**  
   Because a hijacked self-pointer binds cleanly to a syntactically valid command from another user or tenant in the context window, the model's internal probabilities and verbal confidence reports are completely blind to the mix-up (`AUROC 0.5444`, zero cross-validated information gain). Authorization checks and tenant isolation must be enforced by a deterministic policy engine *after* the LLM emits a tool call—never by relying on the model's self-monitoring.
4. **For Model Selection & Routing: Know where the 7B-to-32B boundary lies.**  
   Small, fast 7B models already possess frontier-grade surface fluency (`L_self`), making them look deceptively capable in chat demos. However, multi-hop entity binding (`M_self`) only stabilizes across layers 18+ and requires 14B–32B+ scale (or explicit 0-hop ID injection) whenever multiple actors and state updates share a context window.

Daniel Dennett and Keith Frankish predicted that the "self" would turn out to be a convenient desktop icon painted over distributed machinery. By combining large-scale behavioral stress tests with multi-layer vector surgery, I no longer have to treat that thesis as abstract philosophy—it is now possible to watch the relay baton pass through Layer 18, measure the exact 86.5-degree angle of the illusion in vector space, and design agent architectures so the icon never has a chance to crack.

---

### Dive Into the Full Mathematical Paper & Reproducible Code
Explore the complete technical paper—including full LaTeX derivations, Holm-Bonferroni tables, JumpReLU SAE equations, 28-layer subspace plots, and reproducible `uv` pipelines—in **[`docs/ARTICLE.md`](ARTICLE.md)** and the **[`mechinterp-illusionism` repository](../README.md)**.
