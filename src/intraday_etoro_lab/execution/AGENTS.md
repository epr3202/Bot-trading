# Execution boundary

Read root AGENTS.md and docs/ORDER_LIFECYCLE.md. Preserve the single process
executor lock, durable intent-before-send transaction, unique session entry and
ownership checks. UNKNOWN reserves capacity and cannot be blindly resubmitted.
Pause only disarms entries; reconciliation and protected owned exits remain
available. Never widen stops, over-close a position or equate acknowledgement
with a fill. Test response loss, cancel races, partial fills and restart.
