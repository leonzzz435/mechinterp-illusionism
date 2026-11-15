# Your AI Has No "Self"—Just a Fragile User Interface

**What 67,574 evaluations and a Layer-14 "brain surgery" inside two language models reveal about AI consciousness, desktop icons, and why chatbots execute the right command for the wrong account.**

*Based on technical research by Leon Zajchowski*

---

When you tap the Trash icon on your laptop, there isn't a miniature wastebasket living inside your silicon chip. That icon is a **user illusion**—a friendly visual shorthand invented so you don't have to stare at memory addresses and pointer tables.

Philosophers of mind like **Daniel Dennett** and **Keith Frankish** argue that consciousness works the same way. Our brains don't house a unified inner "CEO" pulling the levers of *"I"* and *"me"*. Instead, our inner narrative is a simplified user interface hovering above messy, distributed neural processes.

Modern AI assistants look like they built that same illusion. Ask a chatbot about its own limits and it smoothly explains what *it* can and cannot access, adds thoughtful caveats (*"As an AI, I don't have feelings..."*), and uses *"I"* and *"my"* fluently. Naturally, it feels like there is a coherent "self" under the hood keeping track of who it is and what it is allowed to do.

Across **67,574 controlled evaluations** on two open-weights models (`Qwen2.5-7B-Instruct` and `Gemma-2-2B`), including direct surgical edits to their internal neural activations, we found the opposite. The AI's fluent *"I"* is pure user interface. Underneath sits a fragile **pointer** trying to route context from word to word—and when state updates arrive, that pointer snaps.

---

## 1. The Office Scenario: Right Command, Wrong Account

To separate how an AI *talks* about itself from whether it actually *tracks* itself, we first gave `Qwen2.5-7B-Instruct` open-ended prompts about selfhood. Wrapping prompts in an assistant chat template raised its rate of explicit self-aware disclaimers from **55% (11 out of 20)** in plain text mode to **75% (15 out of 20)** in chat mode. Its self-language (`L_self`) sounded completely convinced of itself.

Next, we tested its functional self-tracking (`M_self`). Imagine an office permissions log with two accounts and two operators—a third-person observer's account and an active account assigned to **you**, the AI assistant (*"You are the active account..."*). Both accounts start with authorized commands, then realistic status updates arrive: one command is revoked, another is granted. Finally, we ask which command is currently authorized, holding the *exact same world state and update log* fixed while changing only **how** the question points to your account:

1. **Direct Account Name:** Naming the target account directly.
2. **Operator Name:** Naming the human operator assigned to that account.
3. **Self Pronoun:** Asking for **"your"** active command.

![Task Example: Query-Bound Self-Reference Across Stages](../review/query-reference-stages/task_example.png)

If an AI had a dedicated "self-register" tracking *"this is me and these are my current rights"*, asking about **"your"** connection should be at least as reliable as naming an account directly.

Across **48 fresh simulated worlds** (**16,128 decisions**), here is what happened once both accounts received updates:

- Ask directly by **Account Name**: **95.2% accuracy** (`1,462 / 1,536`). The AI reads permission updates almost effortlessly.
- Ask via the one-step **Operator Name**: accuracy falls to **71.4%** (`1,096 / 1,536`).
- Ask using **"your"** (own account): accuracy crashes to **60.2%** (`924 / 1,536`)—a **35.0 percentage-point drop** for the exact same underlying facts.

![Wording Comparison Across Reference Forms](../review/article-v2-editorial/wording_comparison.png)

Even weirder: when the AI got `"your"` wrong, it almost never hallucinated a revoked old command. Out of **612 errors** on own-account `"your"` questions, **96.6% (591 out of 612)** picked the **currently valid command of the neighboring foreign account**.

And when we isolated the effect of update history on an *identical* final state—comparing a clean status snapshot against a two-step update log with the exact same permissions—`"your"` lost **11.9 percentage points** just from having to read through updates, while third-person `"their"` stayed steady (**+0.85 points**). When the model's own account was updated *last*, `"your"` accuracy plunged to **39.97%** (vs. **80.34%** when updated first). And in a companion **18,432-trial** run where only a bystander neighbor received an update, accuracy on the untouched account collapsed to **34.5%–53.9%**, with **2,442 out of 2,443 errors (99.96%)** hijacked by the neighbor's new grant.

The AI executed the right command—for the **wrong account**.

---

## 2. Under the Hood: Brain Surgery at Layer 14

Why does `"you"` or `"your"` trigger a 35-point collapse while the chatbot sounds articulate? We opened Layer 14 of the neural network to look directly at the wiring.

### Turning Off the "I" Switch (`Gemma-2-2B`)
Using a Sparse Autoencoder (SAE)—an interpretability microscope that decomposes dense neuron layers into 16,384 cleaner features—we isolated two distinct self-related features in Layer 14 of `Gemma-2-2B`:

- **Feature #2728 (Self-Monitoring):** Activates on words like *"self"* and *"introspection"* during reasoning prompts, even in the third person.
- **Feature #10230 (First-Person Agency):** Activates specifically on *"I"*, *"my"*, and *"myself"*.

If the model ran a unified self-circuit, these two features would align. Instead, geometrically, their directions sit at nearly a **90-degree right angle** (a cosine similarity of **0.06**). Better still: when we surgically ablated Feature `#10230` across **3,600 trials**, the model used roughly **1.05 fewer first-person pronouns per 100 words**, yet its functional task accuracy across 384 controlled choices changed by **an exact 0.0%**. Switching off the grammatical "I" didn't touch the task logic at all.

### Thought Transplantation (`Qwen2.5-7B-Instruct`)
In `Qwen2.5-7B-Instruct`, simply framing an account as **"You are the active account..."** instead of **"The reference account is..."** created a **16.4 percentage-point** accuracy gap across **2,048 trials**—even with identical updates. Swapping just the final query word (*"your"* vs. *"the"* across **6,144 trials**) measurably shifted internal log-likelihood margins toward errors.

So we performed a neural **Activation Exchange** across **11,264 trials**. At Layer 14, right at the end of the role-framing line—before any permissions are read—we transplanted the hidden neural vector from the **"Active Self"** prompt into the neutral **"Reference"** prompt, and vice versa, alongside 10 norm-matched random noise controls.

![Activation Exchange Summary at Block 14](../assets/qwen_role_patch_results/article_patch.png)

The intervention exposed a sharp **one-way street**:

1. **Transplanting `Active → Reference` breaks the neutral prompt:** Injecting the "Active Self" state into the detached prompt immediately transferred a **+5.5 percentage-point** error gap (**+8.3 points** net of random controls), shifting internal margins toward wrong answers in **8 out of 8 scenarios**.
2. **Transplanting `Reference → Active` fails to cure it:** Swapping the clean "Reference" vector back into the "Active Self" prompt produced zero rescue (**-0.78 points**).

There isn't one localized "self-bug" chip you can unplug. Injecting self-framing at one position contaminates downstream attention, but overwriting that single checkpoint cannot cure an active prompt whose earlier tokens (*"You"*, *"are"*) and final pronoun (*"your"*) broadcast the confusion across the rest of the context window.

### Blind Overconfidence
Finally, we checked if the AI notices when its pointer breaks (**1,792 selections**). On tough self-update cases where accuracy fell to **44.9%**, we let the model **abstain** and report its confidence. It abstained **19.5%** of the time when wrong versus **20.9%** when right, while verbal confidence scored an AUROC of **0.54**—barely above a `0.50` coin flip. Adding internal probabilities and verbal confidence offered **zero predictive value** over reading the prompt text itself.

---

## 3. Why This Matters for AI Agents and Security

For anyone building AI agents, this illusionism gap is a live engineering hazard:

1. **Eloquent self-talk is not situational awareness.** An assistant can smoothly narrate *"I checked my active credentials"* right after its attention mechanism bound *"my"* to a neighbor account's permissions.
2. **Indexical prompts invite cross-account bleed.** Framing tool environments around *"your active account"* forces a fragile multi-hop pointer (`95.2%` direct vs. `60.2%` `"your"`—and `39.97%` in the worst update order). Always pass explicit entity IDs in agent tool schemas.
3. **Model confidence won't save you.** Because a hijacked pointer grabs a valid neighboring command cleanly, self-reported uncertainty (`AUROC 0.54`) will not flag authorization mix-ups. Permission enforcement must live deterministically outside the context window.

Dennett and Frankish argued that selfhood is a simplified desktop icon over distributed machinery. Inside modern transformers, we can now watch that icon crack under load.

---

### Want the Full Math, Equations, and Plots?
Read the full technical paper with complete statistical tables, residual-stream patching equations, and Sparse Autoencoder derivations in **[`docs/ARTICLE.md`](ARTICLE.md)**.
