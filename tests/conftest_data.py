"""Explicit importable shared fixture helper; no automatic global fixture registration."""

from functools import lru_cache

from intraday_etoro_lab.data import DataBundle, FixtureProvider


@lru_cache(maxsize=1)
def fixture_bundle() -> DataBundle:
    return FixtureProvider().load()
