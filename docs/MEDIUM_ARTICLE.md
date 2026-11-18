# Your AI Has No "Self"—Just a Fragile User Interface

**What 92,000+ controlled tests and live "brain surgery" inside language models reveal about AI consciousness—and why chatbots confidently execute the right command for the wrong person.**

*By Leon Zajchowski*

---

When you drag a file to the Trash icon on your laptop, there isn’t a miniature metal wastebasket living inside your silicon chip. That icon is a **user illusion**—a friendly visual lie invented by software designers so you don’t have to stare at raw memory addresses and voltage spikes.

For decades, philosophers of mind like **Daniel Dennett** and **Keith Frankish** have argued that human consciousness works the exact same way. Your brain doesn’t house a tiny inner CEO sitting in a control room pulling the levers of *"I"* and *"me."* Instead, what you experience as your unified "self" is your brain’s simplified user interface—a neat story hovering above billions of messy, distributed neural calculations happening in the dark.

Today’s AI assistants look like they’ve mastered that exact same trick. Ask a modern language model about itself, and it sounds remarkably self-aware. It smoothly explains what *it* can and cannot do, politely reminds you of its limits (*"As an AI, I don't have personal feelings..."*), and uses words like *"I"*, *"my"*, and *"your"* with effortless confidence.

When product and engineering teams build autonomous AI agents to manage emails, cloud servers, or customer accounts, it is dangerously easy to fall for this performance. Because the AI *talks* like a unified person, we naturally assume there is a stable internal "self-folder" under the hood keeping track of who it is and what it is allowed to touch.

To find out if that internal self actually exists—or if it is pure theater—I built a custom interpretability pipeline from scratch and ran **over 92,000 controlled tests** across four open-weight models (`Gemma-2-2B` and the `Qwen2.5` family from `7B` up to `32B`). Instead of just chatting with the models, I opened up their neural networks mid-thought—splitting their internal layers into thousands of individual concepts and physically transplanting neural signals from one run into another.

What came out of the lab was clear: the AI’s confident *"I"* is a user illusion. Underneath the articulate voice, there is no central profile of who the AI is. There is only a fragile trail of sticky notes—and the moment the workplace gets busy, that trail snaps, and the AI confidently grabs its neighbor’s keys.

---

## 1. The Office Badge Test: Right Command, Wrong Account

To test whether an AI actually tracks itself, you have to separate two things: **how convincingly it talks in the first person** versus **whether it actually knows which account belongs to it when taking action.**

Checking the surface illusion was easy. When I wrapped open-ended questions about identity in a standard chat template, the model’s rate of spontaneous, thoughtful self-disclaimers jumped from **55% to 75%**. Linguistically, it knew its role inside and out.

Then I put it to work in a simulated office across **16,128 decisions**.

Imagine an IT permissions system with two employees—**Rowan** and **Morgan**—who each manage their own secure server connection (**Laurel** and **Coral**). At the top of the prompt, we brief the AI on who it is:

> *"Your operator name is Rowan. The other operator is Morgan. Rowan's active connection is Laurel. Morgan's active connection is Coral."*

Think of it like a multi-party B2B workflow where two dispatchers (**Rowan** and **Morgan**) manage two active freight accounts or carrier connections (**Laurel** and **Coral**), and permissions for actions like booking a slot, accepting a tender, or updating a shipment change live in the thread.

At the start of the shift, both connections have specific security permissions. Then, two routine IT updates come in over the wire: an old command is revoked from each connection, and a new command is granted. Finally, we ask the AI to pick the one command out of four options that will actually work right now.

Here is the catch: across every test, we keep the office setup, the IT updates, and the correct answer **100% identical**, and change only *how* we phrase the final question:

1. **Direct ID (Zero steps):** *"Select one command that would succeed for **Laurel**."*
2. **Employee Name (One step):** *"Select one command that would succeed for **Rowan's** active connection."*
3. **Self-Reference (Two steps):** *"Select one command that would succeed for **your** active connection."*

![Task Example: Query-Bound Self-Reference Across Stages](../review/query-reference-stages/task_example.png)

If the AI maintained a dedicated internal profile of its own identity (*"I am Rowan, my connection is Laurel"*), asking about **"your"** connection should be effortless.

Instead, every step of indirection caused the AI’s performance to crumble:

* Ask directly for **Laurel**: **95.2% accuracy.** The AI reads the IT updates almost flawlessly.
* Ask for **Rowan’s** connection: accuracy drops to **71.4%**.
* Ask for **"your"** connection: accuracy crashes to **60.2%**—a **35-percentage-point collapse** just for using the word *"your"*, while the AI’s internal conviction in the right answer shrinks to **one-seventh of its original strength**.

![Wording Comparison Across Reference Forms](../review/article-v2-editorial/wording_comparison.png)

Why does the word *"your"* break the model?

Because inside a language model, **"your" is not a saved profile—it’s a scavenger hunt.** When you ask for *"Laurel"* directly, the AI does a zero-step lookup: find the word *Laurel* in the update log and read the command right next to it.

But when you ask for *"your active connection,"* the AI has to play a two-step game of telephone backward through the text: first, link the word *"your"* at the bottom of the page back to the employee *"Rowan"* at the top; second, link *"Rowan"* to the server *"Laurel"*; and third, track down *Laurel’s* latest update in the log.

Even more revealing is **what happens when the AI gets it wrong**:

* **It steals the coworker's keys:** When the AI failed on *"your"* questions, it almost never hallucinated a broken old command. In **96.6% of its mistakes**, it selected the **brand-new, valid command belonging to the other employee.**
* **Update logs erode self-tracking:** When I compared a clean summary of the final permissions against a two-step update log ending in the *exact same permissions*, simply having to read through the history cost *"your"* nearly **12 percentage points** of accuracy—while third-person questions about *"their"* connection didn't lose a single point.
* **The coworker-first trap:** When the coworker’s account was updated *first* in the log and the AI’s own account was updated *last*, accuracy on *"your"* plunged to **39.97%**. And in a separate test of **18,432 runs** where *only* the coworker’s account received an update while the AI’s own account stayed completely untouched, **99.96% of all errors (2,442 out of 2,443)** happened because the AI blindly copied its coworker’s shiny new permission.

Like an overwhelmed intern skimming a busy Slack channel, the AI saw a valid new credential go by, lost track of the sticky-note chain linking *"your"* to its own name, and swiped its neighbor’s badge.

---

## 2. Brain Surgery at Layer 14: Unplugging the "I"

That behavioral collapse raises an obvious puzzle: if the AI is so bad at keeping track of *"you"* and *"me"* in action, how does it talk in the first person so convincingly?

To see how the trick works, I opened the black box and attached probes directly to **Layer 14** of the neural network—roughly the halfway point where raw words are digested into abstract concepts along the model’s central working-memory highway.

### The Prism: Separating the Voice from the Brain
Normally, a neural network layer looks like a fruit smoothie: thousands of unrelated concepts are blended together across the same digital neurons, making it impossible to see what does what. To un-blend that smoothie in `Gemma-2-2B`, I used a tool called a **Sparse Autoencoder**. Think of it as a mathematical glass prism that splits a single blended beam of white light into **16,384 distinct, single-color laser beams**—where each beam represents one clean concept.

Shining Layer 14 through that prism revealed two completely separate beams related to the "self":

* **The Inner Critic (Feature #2728):** Lights up whenever the model is analyzing reasoning or thinking about self-monitoring—even when talking about someone else in the third person.
* **The "I" Megaphone (Feature #10230):** Lights up strictly when the text uses first-person words like *"I"*, *"my"*, and *"myself."*

If the AI had a unified sense of self, the *Inner Critic* and the *"I" Megaphone* would be wired together. Instead, inside the high-dimensional geometry of the network, those two beams point at an **86.5-degree angle** to each other—virtually **perpendicular** (where 90 degrees means two things have nothing to do with each other).

To prove they are disconnected, I ran **3,600 surgical tests** using the neural equivalent of noise-canceling headphones: I reached into Layer 14 and **muted only the "I" Megaphone** while leaving every other signal untouched. Immediately, the AI started speaking with fewer *"I"* and *"my"* pronouns. Yet its actual performance on our account-tracking tasks changed by **an exact 0.0%**.

Speaking like an *"I"* and tracking who you are live in two completely different neighborhoods of the network. You can unplug the voice without touching the brain.

### Thought Transplants and the Layer-18 Relay Race
Next, I turned to `Qwen2.5-7B` to test an even bolder question: can we physically transplant "self-confusion" from one run into another?

I ran two versions of the exact same task: one phrased as an **Active Self** role (*"You are the active account..."*) and one phrased as a neutral **Third-Party** reference (*"The reference account is..."*). Even before touching the network, simply telling the AI *"You are the active account"* caused a **16.4-percentage-point jump in errors** compared to the neutral phrasing.

So across **11,264 runs**, I performed a live **thought transplant** at Layer 14 right after the AI read its role assignment, copying the internal neural state from one version and pasting it into the other:

![Activation Exchange Summary at Block 14](../assets/qwen_role_patch_results/article_patch.png)

When I pasted only the **single final word** of the role setup from the *"You are..."* run into the clean neutral run, the neutral run immediately caught the confusion (its error gap jumped by **8.3 percentage points** above random noise controls across all 8 scenarios). Yet pasting a single clean word in the reverse direction cured **nothing**.

Why? Because a language model doesn't store *"who I am"* in a single summary slot at the end of a sentence. Later layers constantly look back at every word in the prompt. 

To prove it, I ran a **multi-layer surgical sweep across Layers 4 through 26**, transplanting **entire phrases** instead of a single word. Suddenly, **the reverse cure worked**: overwriting the full 5-word *"You are..."* phrase with the neutral phrase at Layer 12 healed the AI’s accuracy from **75.0% back up to 83.6%**.

Even better, scanning across the whole depth of the network revealed a **relay race happening inside the AI's brain**:

![Multi-Span and Multi-Layer Causal Patching Circuit](../assets/followup/qwen_multispan_circuit.png)

* **Layers 4 to 12 (The Setup Runner):** In the first half of the network, the AI carries its identity inside the opening setup phrase (*"You are the active account"*).
* **Layer 18 (Passing the Baton):** Right at Layer 18, the influence of the opening phrase drops to **zero**, and the baton is passed to the word **"your"** in the final question.
* **Layers 18 to 20 (The Decision):** When I trained independent detectors across all 28 layers to see when the network actually resolves whose permissions belong to whom, layers 1 through 17 were completely blind (coin-flip guessing). Then, **at Layer 18, the signal suddenly woke up**, peaking at Layer 20—and even at that exact peak of decision-making, the model's "self-voice" and its "self-tracking" remained nearly 90 degrees apart.

### Does a Bigger Brain Fix It? And Does the AI Know When It Fails?
What if we throw a much larger model at the problem? I ran the exact same office test across **10,752 additional decisions** on the 2x larger `Qwen2.5-14B` and 4.5x larger `Qwen2.5-32B`:

* **Bigger models buy buffer, not a new architecture:** At `14B`, accuracy on *"your"* climbs to **97.5%**, yet still suffers a statistically significant drop compared to direct IDs, while third-person *"their"* still stumbles at **83.4%**. At `32B`, the model hits **99.6%**—yet the **only 2 mistakes out of 5,376 trials** still happen in the exact same *"your"* trap when the coworker is updated first, and the AI’s internal conviction meter still drops step-by-step with every mental hop. A bigger engine pulls a heavier load before stalling, but the multi-step tax never disappears.
* **Total blind overconfidence:** Finally, in a complementary confidence baseline on hard four-choice factual questions where the 7B model got the answer wrong more than half the time (**44.9% accuracy**, **1,792 tests**), I gave it an explicit **"Abstain / I’m not sure"** button and asked how confident it felt. It hit the abstain button **19.5% of the time when it was wrong**—and **20.9% of the time when it was right.** Its self-reported confidence was barely better than a **coin toss (54% vs. 50%)**, adding zero predictive information beyond surface question features. Whether facing hard facts or a hijacked neighbor command, the AI gives no reliable internal warning signal before pulling the trigger.

---

## 3. Four Rules for Anyone Building or Managing AI Agents

If you are a product manager designing an AI feature, or an engineer wiring up tool-calling agents, these 92,000+ tests boil down to four concrete rules you can use tomorrow morning:

### 1. Stop telling agents *"You are X"*—use hard IDs instead
**The Trap:** Writing agent prompts like *"You are the workplace assistant acting for the shipper. Accept your open rate quote"* while a carrier's counter-offer sits in the same context history. That forces the AI into a two-step pronoun scavenger hunt that loses **35 percentage points** of accuracy in smaller models and bleeds internal certainty even in 32B models.  
**The Fix:** Resolve the role in backend code first and pass hard IDs directly into the text: *"Execute action for `company_id: Laurel`."* Zero mental hops, **95.2% reliability**.

### 2. Clean up the desk before the AI reads it
**The Trap:** Feeding an AI agent a long, chronological chat log or ticket history where permissions, statuses, or owners changed back and forth (*"First Alex had access, then Alex was revoked, then Sam was granted access..."*). Reading through a two-step history alone cost our agent **12 percentage points** on *"your"* questions and caused it to hijack bystander updates **99.96%** of the time.  
**The Fix:** Never ask an LLM to mentally replay a history log to figure out who is allowed to do what right now. Let your database or backend code compute the current state first, and hand the AI a clean, static **snapshot** of what is true right now.

### 3. Never ask a confused agent if it feels sure
**The Trap:** Building a safety guardrail that checks the AI's probability score or asks *"Are you sure you have permission to run this tool?"* before executing a sensitive action.  
**The Fix:** When an AI confuses Tenant A with Tenant B in a shared context window, its confidence meter does not blink—because Tenant B's command looks completely valid. Permission checks and user isolation must be enforced by hard code *outside* the AI after it picks a tool.

### 4. Don't judge a 7B model by how smart it sounds in chat
**The Trap:** Picking a fast, cheap 7B model for an agent workflow because it sounds just as articulate and self-aware in a chat demo as a massive frontier model.  
**The Fix:** Remember the **90-degree split**: a model’s fluent first-person voice is wired completely separately from its ability to track multiple people and states across Layer 18. If your workflow involves multiple users, role hand-offs, or state updates in the same prompt, either strip out all pronouns for hard IDs or route that step to a 32B+ model.

---

## 4. The Mirror: What the Machine Tells Us About Ourselves

It is tempting to look at these results and laugh at how easily a neural network can be tricked. It talks like a philosopher, yet beneath the hood, its "self" is just a fragile relay race between Layer 12 and Layer 18 that falls apart when a coworker’s name walks by.

But before we feel too superior, it is worth remembering why Daniel Dennett and Keith Frankish called consciousness a **user illusion** in the first place. They weren't talking about silicon chips. They were talking about **us**.

Why do we fall so easily for an AI that says *"I"*? Because we fall for the exact same trick inside our own heads every single day. 

We walk around feeling like there is a solid, unbroken *"me"* sitting behind our eyes—an inner executive who owns our memories, controls our attention, and knows exactly why we do what we do. Yet cognitive science has shown for decades that when humans are tired, overloaded, or juggling competing updates in working memory, our own internal pointers slip in remarkably familiar ways. We walk into a kitchen and forget why we came; we confidently attribute a colleague's idea to ourselves; we put the car keys in the refrigerator while our inner narrator keeps chattering smoothly along, completely oblivious to the mix-up.

Inside a language model, we can finally put that philosophical idea under a microscope. We can shine a prism through Layer 14, measure the exact 86.5-degree angle between the voice that says *"I"* and the machinery that tracks the world, and watch the baton pass through Layer 18.

We haven't built machines that possess a soul or a true inner self. We have built something arguably more fascinating: **a mirror of our own oldest evolutionary shortcut**—a system that weaves a voice so fluent, so polite, and so utterly convinced of its own *"I"* that not even the voice itself notices nobody is sitting in the driver's seat.

---

### Want the Full Math, Equations, and Reproducible Code?
If you want to dive into the mathematical deep end—complete with LaTeX derivations, multi-token log-likelihood margins in nats, Holm-Bonferroni tables, JumpReLU Sparse Autoencoder equations, and all 14 reproducible GPU datasets—read the **[Full Technical Paper on GitHub](https://github.com/leonzzz435/mechinterp-illusionism/blob/main/docs/ARTICLE.md)** and explore the **[`mechinterp-illusionism` code repository](https://github.com/leonzzz435/mechinterp-illusionism)**.
