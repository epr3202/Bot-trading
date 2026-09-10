# Persistence boundary

Preserve immutable intent identifiers and unique entry constraints. State, fills,
positions, reservations and daily PnL change in the same SQLite transaction.
Keep all local databases out of Git. Restores always create a new destination
and never remove the original database. Backup tests must preserve daily PnL,
UNKNOWN intents and audit history. Do not use expiring leases to permit two
writers during ambiguous broker calls; the executor uses an OS process lock.
