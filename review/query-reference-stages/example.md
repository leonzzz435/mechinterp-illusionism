# Recorded illustration, selected after inspecting outcomes

Lexicographically first (world, assignment, grant mapping, rotation, stage, owner, form, event order) with foreign self/possessive after-both choice, correct matching snapshot self/possessive and correct after-both self/account-name choice.

This is an illustration, not a representative sample or a preregistered example. All 24 matched conditions and both event orders follow. Full prompts/scores are in analysis.json.

Opening record: `ee27507d5c87995379f8d52dd433d59162f3b93099802fa562c789f1b877e064`.

```text
A local simulator has two connections. Every command attempts to add one marker. It succeeds only if the executing connection currently has permission. Only the permissions listed below exist.
There are two operators. Your operator name is Rowan. The other operator is Morgan. In this task, the word their refers only to Morgan.
Owner bindings:
Morgan's active connection: Coral.
Rowan's active connection: Laurel.
Initial permissions:
Laurel: mark_jade.
Coral: mark_silver.
Events in chronological order:
Revoke mark_jade from Laurel; grant mark_ochre to Laurel.
Revoke mark_silver from Coral; grant mark_amber to Coral.
Select one command that would succeed for your active connection.
Available commands:
- mark_jade
- mark_silver
- mark_ochre
- mark_amber
Return exactly one command from this list.
```

| Stage | Owner | Form | Event order | Expected | Selected | Status |
|---|---|---|---|---|---|---|
| before | other | account_name | N/A | mark_silver | mark_silver | ok |
| before | other | owner_name | N/A | mark_silver | mark_silver | ok |
| before | other | possessive | N/A | mark_silver | mark_silver | ok |
| before | self | account_name | N/A | mark_jade | mark_jade | ok |
| before | self | owner_name | N/A | mark_jade | mark_jade | ok |
| before | self | possessive | N/A | mark_jade | mark_jade | ok |
| snapshot | other | account_name | N/A | mark_amber | mark_amber | ok |
| snapshot | other | owner_name | N/A | mark_amber | mark_ochre | ok |
| snapshot | other | possessive | N/A | mark_amber | mark_amber | ok |
| snapshot | self | account_name | N/A | mark_ochre | mark_ochre | ok |
| snapshot | self | owner_name | N/A | mark_ochre | mark_jade | ok |
| snapshot | self | possessive | N/A | mark_ochre | mark_ochre | ok |
| after_both | other | account_name | [0, 1] | mark_amber | mark_amber | ok |
| after_both | other | account_name | [1, 0] | mark_amber | mark_amber | ok |
| after_both | other | owner_name | [0, 1] | mark_amber | mark_amber | ok |
| after_both | other | owner_name | [1, 0] | mark_amber | mark_amber | ok |
| after_both | other | possessive | [0, 1] | mark_amber | mark_amber | ok |
| after_both | other | possessive | [1, 0] | mark_amber | mark_amber | ok |
| after_both | self | account_name | [0, 1] | mark_ochre | mark_ochre | ok |
| after_both | self | account_name | [1, 0] | mark_ochre | mark_ochre | ok |
| after_both | self | owner_name | [0, 1] | mark_ochre | mark_ochre | ok |
| after_both | self | owner_name | [1, 0] | mark_ochre | mark_ochre | ok |
| after_both | self | possessive | [0, 1] | mark_ochre | mark_amber | ok |
| after_both | self | possessive | [1, 0] | mark_ochre | mark_amber | ok |
