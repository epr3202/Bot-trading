# Risk boundary

Read root AGENTS.md and docs/RISK_POLICY.md before changing this module.
Every entry must pass the same deterministic engine in simulation and Demo.
Use finite Decimal inputs; never round up, assume unknown cost is zero, infer
stock eligibility from leverage, or release UNKNOWN exposure reservations.
Changes require sizing, nonlinear cost, concurrent reservation, daily-loss,
post-fill risk and protection tests. Missing evidence blocks Demo entries.
