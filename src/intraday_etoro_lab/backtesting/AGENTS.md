# Research replay safety

Read docs/BACKTEST_PROTOCOL.md and STRATEGY_SPEC.md. Use identical strategy and risk
modules for offline replay; never execute brokers. Submission sees available events,
bar-only fills occur at a strictly later open. Stop ambiguities favor adverse outcomes.
Include sessions with no trades, full costs, data/config/calendar identifiers, and
synthetic labels. Late revisions cannot rewrite past decisions. Undefined metrics stay
null with explanations. Test manual arithmetic and future-data perturbations.
