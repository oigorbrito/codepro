# 0010 — P8.2 minimal mechanism trial boundary

- Status: experimental contract
- Date: 2026-09-22

P8.2 adds only a declarative A/B/C/D trial plan over the P8.1 qualification
contracts. The executor and all comparability controls are fixed in one config;
only treatment varies across generated trial plans. The harness does not run
LLMs, switch executors, apply mechanisms, infer acceptance, or promote a
mechanism.

Safe editor and enhanced repository context are donors under trial, not Arkx
dependencies. The P8.2 plan preserves missing values as unknown and leaves
independent acceptance authority outside the harness.
