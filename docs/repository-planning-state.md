# P4 repository planning / state

P4 creates deterministic `RepositoryState` and `RepositoryPlan` artifacts from explicit structure. It does not execute plans, change policy, alter acceptance, or promote a result.

Collections are normalized for deterministic JSON. Plan steps have stable identities and explicit dependencies. Unknown dependencies and cycles are rejected. A step is never marked `COMPLETED` by textual assertion or by plan creation.

`ReplanRequest` and `ReplanResult` preserve `previous_plan_ref`; a new plan cannot silently replace its predecessor. Replanning is a contract, not an autonomous loop.

```text
REPOSITORY_WIDE_PATH != PLANNER_EXECUTED
P4_OFF is supported
```

The fixture is `REPOSITORY_PLANNING_FIXTURE`, not a performance claim.

