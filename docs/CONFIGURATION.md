# Configuración

Fuente de verdad: modelos Pydantic y configs/offline.yaml. Campos extra se rechazan.
Números monetarios son Decimal USD; fracciones son proporciones (0.001 = 0,10%).
Todos los costes predeterminados describen únicamente simulación sintética.

| Clave | Tipo | Valor predeterminado |
|---|---|---|
| `mode` | enum 'Mode' | `offline` |
| `order_submission_enabled` | class 'bool' | `False` |
| `runtime_dir` | class 'pathlib.Path' | `runtime` |
| `reports_dir` | class 'pathlib.Path' | `reports\runs` |
| `arm_ttl_seconds` | class 'int' | `300` |
| `strategy.version` | typing.Literal['ORB_RVOL_v0.1', 'ORB_BASE_v0.1', 'ORB_RVOL_v1.0'] | `ORB_RVOL_v0.1` |
| `strategy.warmup_sessions` | typing.Literal[20] | `20` |
| `strategy.opening_range_minutes` | typing.Literal[5] | `5` |
| `strategy.min_previous_close` | class 'decimal.Decimal' | `10` |
| `strategy.min_average_dollar_volume` | class 'decimal.Decimal' | `50000000` |
| `strategy.min_rvol` | class 'decimal.Decimal' | `2` |
| `strategy.max_selected` | class 'int' | `10` |
| `strategy.entry_window_minutes` | class 'int' | `60` |
| `strategy.selection_wait_seconds` | class 'int' | `2` |
| `strategy.signal_ttl_seconds` | class 'int' | `10` |
| `strategy.relative_strength_enabled` | class 'bool' | `False` |
| `strategy.regime_enabled` | typing.Literal[False] | `False` |
| `strategy.vwap_enabled` | typing.Literal[False] | `False` |
| `strategy.rs_benchmarks` | tuple[typing.Literal['SPY'], typing.Literal['QQQ']] | `('SPY', 'QQQ')` |
| `strategy.rs_comparison` | typing.Literal['strictly_greater_than_both'] | `strictly_greater_than_both` |
| `strategy.rs_margin` | class 'decimal.Decimal' | `0` |
| `strategy.etf_tradable` | typing.Literal[False] | `False` |
| `strategy.benchmarks_reference_only` | typing.Literal[True] | `True` |
| `risk.allocated_capital` | class 'decimal.Decimal' | `10000` |
| `risk.risk_fraction` | class 'decimal.Decimal' | `0.001` |
| `risk.daily_loss_fraction` | class 'decimal.Decimal' | `0.005` |
| `risk.max_positions` | class 'int' | `2` |
| `risk.max_gross_fraction` | class 'decimal.Decimal' | `1` |
| `risk.max_position_fraction` | class 'decimal.Decimal' | `0.60` |
| `risk.max_spread_fraction` | class 'decimal.Decimal' | `0.003` |
| `risk.max_price_deviation` | class 'decimal.Decimal' | `0.005` |
| `risk.max_source_divergence` | class 'decimal.Decimal' | `0.005` |
| `risk.max_quote_age_seconds` | class 'int' | `3` |
| `risk.signal_ttl_seconds` | class 'int' | `10` |
| `costs.known` | class 'bool' | `True` |
| `costs.fixed_per_side` | class 'decimal.Decimal' | `0` |
| `costs.minimum_per_side` | class 'decimal.Decimal' | `0` |
| `costs.per_unit_per_side` | class 'decimal.Decimal' | `0.005` |
| `costs.notional_rate_per_side` | class 'decimal.Decimal' | `0` |
| `costs.slippage_per_unit` | class 'decimal.Decimal' | `0.02` |
| `costs.quadratic_impact` | class 'decimal.Decimal' | `0` |
| `backtest.starting_capital` | class 'decimal.Decimal' | `10000` |
| `backtest.latency_ms` | class 'int' | `250` |
| `backtest.spread_bps` | class 'decimal.Decimal' | `2` |
| `backtest.slippage_bps` | class 'decimal.Decimal' | `1` |
| `backtest.seed` | class 'int' | `42` |
| `backtest.bootstrap_samples` | class 'int' | `200` |
| `backtest.bootstrap_block_sessions` | class 'int' | `2` |
| `data.provider` | typing.Literal['fixtures', 'import', 'massive'] | `fixtures` |
| `data.path` | pathlib.Path o None | `None` |
| `data.manifest` | pathlib.Path o None | `None` |

*_seconds usa segundos; latency_ms milisegundos; *_bps puntos básicos.
Cambios de modo, datos, estrategia, costes, riesgo y duración alteran el hash de
configuración y requieren nuevo armado. Presupuesto backtest y riesgo, y TTL de
estrategia/riesgo, deben coincidir. Extensiones bool solo admiten false en v0.1.
Strategy 1 v1 usa configs/strategy-1-v1.yaml: RS activa contra SPY y QQQ;
regime/VWAP desactivados, ETF excluidos. Versión, parámetros, riesgo y costes
se validan como contrato congelado; strategy_hash excluye datos y backtest.

BOT_MODE se valida aun si CLI proporciona otro modo. ORDER_SUBMISSION_ENABLED
solo admite texto true/false y requiere etoro_demo para true. .env no se carga.
ETORO_API_KEY/ETORO_USER_KEY no pertenecen al YAML. El host eToro es fijo.

Esquema completo con límites y tipos: [config.schema.json](config.schema.json).
El panel solo admite host 127.0.0.1, puerto 1024–65535; 8765 por defecto.
