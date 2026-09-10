# Data safety

Read root AGENTS and docs/DATA_CONTRACTS.md before changes. Raw imports are immutable;
never fill missing OHLCV, infer consolidated volume, or invent broker identifiers.
Evaluate only events available by the decision time; keep late revisions auditable.
Calendar fixtures must cover DST, holidays and early close. Changing fixture profits
never validates alpha. Run data/strategy tests and the integrated offline replay.
