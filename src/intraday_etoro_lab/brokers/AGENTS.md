# Broker safety

Read root AGENTS and docs/ETORO_API_AUDIT.md before transport changes.
Only the enumerated official Demo mutation contracts are allowed. Never add
arbitrary hosts, redirects, authentication fallbacks or implicit write retries.
Mocks do not establish broker connectivity. Preserve UNKNOWN and ownership.
Bootstrap never activates external reads of accounts or trading writes.
