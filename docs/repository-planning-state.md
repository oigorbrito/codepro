# P4 repository planning / state

P4 creates deterministic `RepositoryState` and `RepositoryPlan` artifacts from explicit structure. It does not execute plans, change policy, alter acceptance, or promote a result.

Schema v2 hardens plan-state semantics:

- completed and remaining step sets cannot overlap;
- plan creation requires an explicit goal, at least one step, and acceptance criteria;
- plan creation can only create `PENDING` steps and therefore cannot assert execution progress;
- unknown dependencies and cycles are rejected;
- replanning requires evidence and an explicit previous-plan reference;
- an exhausted replan budget cannot produce a new `ReplanResult`.

A new plan cannot silently replace its predecessor. Replanning is a contract, not an autonomous loop.

```text
PLAN_CREATED != STEP_EXECUTED
STEP_DECLARED != STEP_COMPLETED
REPLAN_REQUESTED != REPLAN_AUTHORIZED
REPOSITORY_WIDE_PATH != PLANNER_EXECUTED
```

The fixture is `REPOSITORY_PLANNING_FIXTURE`, not a performance claim.
