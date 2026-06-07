import os
import logging
import datetime
import threading
import requests
from typing import TypedDict


SUPPORTED_SYMBOLS = ["BTC", "ETH", "SOL", "AVAX"]

# Static fallback map of validated SoSoValue currency_ids resolved live from
# /currencies during integration testing. Used to skip the rate-limited
# /currencies endpoint and call /market-snapshot directly. Refreshed
# opportunistically when the cache becomes stale and a non-rate-limited
# /currencies call succeeds.
_STATIC_CURRENCY_IDS: dict[str, str] = {
    "BTC": "1673723677362319866",
    "ETH": "1673723677362319867",
    "SOL": "1673723677362319875",
    "AVAX": "1673723677362319883",
}

_CURRENCY_ID_CACHE: dict[str, str] = dict(_STATIC_CURRENCY_IDS)
_CURRENCY_ID_CACHE_TS: float = 0.0
_CURRENCY_ID_CACHE_TTL_SECONDS: float = 60 * 60 * 12
_CURRENCY_ID_LOCK = threading.Lock()

SOSOVALUE_CONNECT_TIMEOUT = 3
SOSOVALUE_READ_TIMEOUT = 5
SODEX_CONNECT_TIMEOUT = 3
SODEX_READ_TIMEOUT = 5
ASSET_NAMES = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "AVAX": "Avalanche",
}
SODEX_PAIR_MAP = {
    "BTC": "vBTC_vUSDC",
    "ETH": "vETH_vUSDC",
    "SOL": "vSOL_vUSDC",
    "AVAX": "vAVAX_vUSDC",
}

SOSOVALUE_BASE = "https://openapi.sosovalue.com/openapi/v1"
SODEX_TICKERS_URL = "https://testnet-gw.sodex.dev/api/v1/spot/markets/tickers"


class NormalizedQuote(TypedDict):
    symbol: str
    name: str
    price: float
    change_24h: float
    volume_24h: float
    market_cap: float
    source: str
    timestamp: str


class ProviderResult(TypedDict):
    name: str
    kind: str
    status: str
    latency_ms: int
    last_check: str
    message: str
    quotes: dict[str, NormalizedQuote]


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def _get_sosovalue_key() -> str | None:
    return os.getenv("SOSOVALUE_API_KEY") or os.getenv("SOSO_API_KEY")


class _RateLimitedError(Exception):
    pass


def _resolve_currency_ids(headers: dict) -> dict[str, str]:
    """Return cached BTC/ETH/SOL/AVAX currency_ids.

    The cache is pre-seeded from a static fallback map of validated currency_ids,
    so we never need to call the rate-limited /currencies endpoint to start
    fetching live snapshots. We only attempt an opportunistic refresh when the
    cache TTL has expired, and any failure (especially 429) is non-fatal — we
    fall back to the existing cached/static IDs.
    """
    global _CURRENCY_ID_CACHE_TS
    now = datetime.datetime.now().timestamp()
    with _CURRENCY_ID_LOCK:
        cached = dict(_CURRENCY_ID_CACHE)
        cache_age = now - _CURRENCY_ID_CACHE_TS
    have_full = cached and all(s in cached for s in SUPPORTED_SYMBOLS)
    if have_full and cache_age < _CURRENCY_ID_CACHE_TTL_SECONDS:
        return cached
    # Opportunistic refresh — never block live ingestion if /currencies fails.
    try:
        cur_resp = requests.get(
            f"{SOSOVALUE_BASE}/currencies",
            headers=headers,
            timeout=(SOSOVALUE_CONNECT_TIMEOUT, SOSOVALUE_READ_TIMEOUT),
        )
        if cur_resp.status_code == 429:
            if have_full:
                return cached
            raise _RateLimitedError("HTTP 429 on /currencies (rate limited)")
        cur_resp.raise_for_status()
        cur_envelope = cur_resp.json()
        if cur_envelope.get("code") != 0:
            if have_full:
                return cached
            raise RuntimeError(
                f"currencies error: {cur_envelope.get('message')}"
            )
        currencies = cur_envelope.get("data") or []
        ids: dict[str, str] = {}
        for item in currencies:
            sym = (item.get("symbol") or "").upper()
            if sym in SUPPORTED_SYMBOLS and sym not in ids:
                ids[sym] = item["currency_id"]
        missing = [s for s in SUPPORTED_SYMBOLS if s not in ids]
        if missing:
            if have_full:
                return cached
            raise RuntimeError(f"Missing currency ids for: {missing}")
        with _CURRENCY_ID_LOCK:
            _CURRENCY_ID_CACHE.clear()
            _CURRENCY_ID_CACHE.update(ids)
            globals()["_CURRENCY_ID_CACHE_TS"] = now
        return ids
    except _RateLimitedError:
        logging.exception("Unexpected error")
        raise
    except Exception as e:
        if have_full:
            logging.exception(
                f"Currency-id refresh failed; using cached/static ids: {e}"
            )
            return cached
        raise


def fetch_sosovalue() -> ProviderResult:
    name = "SoSoValue"
    kind = "Market Data"
    started = datetime.datetime.now()
    key = _get_sosovalue_key()
    if not key:
        return {
            "name": name,
            "kind": kind,
            "status": "error",
            "latency_ms": 0,
            "last_check": _now_iso(),
            "message": "Missing SOSOVALUE_API_KEY env var",
            "quotes": {},
        }
    headers = {"x-soso-api-key": key, "Accept": "application/json"}
    try:
        ids = _resolve_currency_ids(headers)
        quotes: dict[str, NormalizedQuote] = {}
        rate_limited = False
        for symbol in SUPPORTED_SYMBOLS:
            cid = ids.get(symbol)
            if not cid:
                continue
            r = requests.get(
                f"{SOSOVALUE_BASE}/currencies/{cid}/market-snapshot",
                headers=headers,
                timeout=(SOSOVALUE_CONNECT_TIMEOUT, SOSOVALUE_READ_TIMEOUT),
            )
            if r.status_code == 429:
                rate_limited = True
                break
            r.raise_for_status()
            payload = r.json()
            if payload.get("code") != 0:
                raise RuntimeError(
                    f"snapshot error for {symbol}: {payload.get('message')}"
                )
            snap = payload.get("data") or {}
            price = float(snap.get("price") or 0.0)
            change_pct = float(snap.get("change_pct_24h") or 0.0) * 100.0
            volume = float(snap.get("turnover_24h") or 0.0)
            mcap = float(snap.get("marketcap") or 0.0)
            if price <= 0:
                continue
            quotes[symbol] = {
                "symbol": symbol,
                "name": ASSET_NAMES[symbol],
                "price": price,
                "change_24h": change_pct,
                "volume_24h": volume,
                "market_cap": mcap,
                "source": name,
                "timestamp": _now_iso(),
            }
        latency = int(
            (datetime.datetime.now() - started).total_seconds() * 1000
        )
        if rate_limited and not quotes:
            return {
                "name": name,
                "kind": kind,
                "status": "error",
                "latency_ms": latency,
                "last_check": _now_iso(),
                "message": "Rate limited (HTTP 429) — using SoDEX fallback",
                "quotes": {},
            }
        if not quotes:
            return {
                "name": name,
                "kind": kind,
                "status": "error",
                "latency_ms": latency,
                "last_check": _now_iso(),
                "message": "No valid snapshots returned",
                "quotes": {},
            }
        msg = (
            f"Resolved {len(quotes)} assets in {latency}ms"
            if not rate_limited
            else f"Partial: {len(quotes)} assets ({latency}ms) — 429 hit"
        )
        return {
            "name": name,
            "kind": kind,
            "status": "connected" if not rate_limited else "error",
            "latency_ms": latency,
            "last_check": _now_iso(),
            "message": msg,
            "quotes": quotes,
        }
    except _RateLimitedError as e:
        logging.exception("Unexpected error")
        latency = int(
            (datetime.datetime.now() - started).total_seconds() * 1000
        )
        return {
            "name": name,
            "kind": kind,
            "status": "error",
            "latency_ms": latency,
            "last_check": _now_iso(),
            "message": "Rate limited (HTTP 429) — using SoDEX fallback",
            "quotes": {},
        }
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        latency = int(
            (datetime.datetime.now() - started).total_seconds() * 1000
        )
        msg = (
            "Rate limited (HTTP 429) — using SoDEX fallback"
            if status == 429
            else f"HTTP {status}: {str(e)[:120]}"
        )
        logging.exception(f"SoSoValue HTTP error: {e}")
        return {
            "name": name,
            "kind": kind,
            "status": "error",
            "latency_ms": latency,
            "last_check": _now_iso(),
            "message": msg,
            "quotes": {},
        }
    except requests.Timeout as e:
        latency = int(
            (datetime.datetime.now() - started).total_seconds() * 1000
        )
        logging.exception(f"SoSoValue timeout: {e}")
        return {
            "name": name,
            "kind": kind,
            "status": "error",
            "latency_ms": latency,
            "last_check": _now_iso(),
            "message": f"Timeout after {latency}ms — using SoDEX fallback",
            "quotes": {},
        }
    except Exception as e:
        logging.exception(f"SoSoValue fetch error: {e}")
        latency = int(
            (datetime.datetime.now() - started).total_seconds() * 1000
        )
        return {
            "name": name,
            "kind": kind,
            "status": "error",
            "latency_ms": latency,
            "last_check": _now_iso(),
            "message": f"{type(e).__name__}: {str(e)[:140]}",
            "quotes": {},
        }


def fetch_sodex() -> ProviderResult:
    name = "SoDEX"
    kind = "Market Data"
    started = datetime.datetime.now()
    try:
        resp = requests.get(
            SODEX_TICKERS_URL,
            headers={"Accept": "application/json"},
            timeout=(SODEX_CONNECT_TIMEOUT, SODEX_READ_TIMEOUT),
        )
        resp.raise_for_status()
        envelope = resp.json()
        if envelope.get("code") != 0:
            raise RuntimeError(f"sodex error: {envelope.get('message')}")
        rows = envelope.get("data") or []
        by_symbol = {row.get("symbol"): row for row in rows}
        quotes: dict[str, NormalizedQuote] = {}
        for symbol in SUPPORTED_SYMBOLS:
            pair = SODEX_PAIR_MAP[symbol]
            row = by_symbol.get(pair)
            if not row:
                continue
            try:
                price = float(row.get("lastPx") or 0.0)
                change_pct = float(row.get("changePct") or 0.0)
                volume_quote = float(row.get("quoteVolume") or 0.0)
            except (TypeError, ValueError):
                continue
            quotes[symbol] = {
                "symbol": symbol,
                "name": ASSET_NAMES[symbol],
                "price": price,
                "change_24h": change_pct,
                "volume_24h": volume_quote,
                "market_cap": 0.0,
                "source": name,
                "timestamp": _now_iso(),
            }
        latency = int(
            (datetime.datetime.now() - started).total_seconds() * 1000
        )
        if not quotes:
            return {
                "name": name,
                "kind": kind,
                "status": "error",
                "latency_ms": latency,
                "last_check": _now_iso(),
                "message": "No matching tickers returned",
                "quotes": {},
            }
        return {
            "name": name,
            "kind": kind,
            "status": "connected",
            "latency_ms": latency,
            "last_check": _now_iso(),
            "message": f"Mapped {len(quotes)} pairs in {latency}ms",
            "quotes": quotes,
        }
    except Exception as e:
        logging.exception(f"SoDEX fetch error: {e}")
        latency = int(
            (datetime.datetime.now() - started).total_seconds() * 1000
        )
        return {
            "name": name,
            "kind": kind,
            "status": "error",
            "latency_ms": latency,
            "last_check": _now_iso(),
            "message": f"{type(e).__name__}: {str(e)[:140]}",
            "quotes": {},
        }


def fetch_all_providers() -> list[ProviderResult]:
    return [fetch_sosovalue(), fetch_sodex()]


def merge_quotes(results: list[ProviderResult]) -> list[NormalizedQuote]:
    """Merge quotes preferring SoSoValue (first successful provider),
    falling back per-symbol to subsequent providers."""
    merged: dict[str, NormalizedQuote] = {}
    for r in results:
        for sym, q in r["quotes"].items():
            if sym not in merged:
                merged[sym] = q
    ordered: list[NormalizedQuote] = []
    for sym in SUPPORTED_SYMBOLS:
        if sym in merged:
            ordered.append(merged[sym])
    return ordered