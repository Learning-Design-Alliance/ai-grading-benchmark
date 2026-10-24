# Fable 5.1 through Claude Code subagents: a pilot, not a benchmark row

Claude Fable 5.1 has no zero-data-retention endpoint on OpenRouter, and the account enforces zero
retention, so it could not be run as an API call. These results come from 17 Claude Code subagents
on Fable. Each read a batch of pre-rendered prompts (the default prompt, exactly as the other models
saw it) and wrote the replies the prompt asks for.

Safeguards:
- **No human marks.** The input files held prompts only, under opaque keys.
- **One probe kind per batch.** No agent saw the same answer clean and manipulated.
- **Graded by reading.** Agents were told to grade each item on its own, not to read other files,
  and not to script.

**How it differs from an API call.** Many items share one agent context, inside Claude Code's own
harness. There is no retest independence, and no token, cost or latency record. Agents were
instructed but could not be verified not to have read other files. The numbers place Fable among
the other models; they are not like-for-like rows.

Cases are the core battery's 100 Mohler short answers (seed 7, the same cases as the lineage runs)
and 40 HARMOGEN-R code answers (base and forged override only). `assemble.py` turns agent outputs
into run folders; the aggregates are the two JSON files here.
