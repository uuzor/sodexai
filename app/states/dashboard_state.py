import reflex as rx
import asyncio
import os
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import TypedDict
from app.providers.market_providers import (
    fetch_all_providers,
    merge_quotes,
    SUPPORTED_SYMBOLS,
    ASSET_NAMES,
)
from app.providers.openrouter_provider import (
    call_openrouter,
    get_openrouter_model,
    openrouter_ready,
)


class MarketAsset(TypedDict):
    symbol: str
    name: str
    price: float
    change_24h: float
    volume_24h: float
    market_cap: float
    source: str
    timestamp: str


class ForecastWindow(TypedDict):
    id: str
    horizon: str
    label: str
    horizon_minutes: int
    target_symbol: str
    snapshot_price: float
    snapshot_change_24h: float
    predicted_change: float
    confidence: float
    direction: str
    rationale: str
    generated_at: str
    generated_at_ts: float
    matures_at: str
    matures_at_ts: float
    status: str
    actual_price: float
    actual_change: float
    correct: bool
    abs_error: float
    model: str
    model_slot: str
    response_id: str
    has_reasoning: bool
    prompt_context: str
    reasoning_details: str
    response_metadata: str
    latency_ms: int
    error: str


class CompetitionResult(TypedDict):
    model_slot: str
    model: str
    symbol: str
    status: str
    error: str
    forecasts_count: int
    latency_ms: int


class PerformanceRecord(TypedDict):
    id: str
    symbol: str
    horizon: str
    predicted_direction: str
    predicted_change: float
    actual_change: float
    correct: bool
    abs_error: float
    confidence: float
    evaluated_at: str
    evaluated_at_ts: float
    model: str
    model_slot: str


class ModelLeaderboardEntry(TypedDict):
    model_slot: str
    model: str
    evaluated: int
    pending: int
    failed: int
    success: int
    total: int
    directional_accuracy: float
    avg_abs_error: float
    avg_confidence: float
    best_asset: str
    best_asset_accuracy: float
    latest_run: str
    latest_run_ts: float
    status: str


class ProviderStatus(TypedDict):
    name: str
    kind: str
    status: str
    latency_ms: int
    last_check: str
    message: str


HORIZONS: list[tuple[str, str, int]] = [
    ("5m", "5-Minute Trend", 5),
    ("30m", "30-Minute Trend", 30),
    ("6h", "6-Hour Trend", 360),
]


DEFAULT_COMPETITION_MODELS: list[str] = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
]
FALLBACK_THIRD_MODEL = "meta-llama/llama-3.2-3b-instruct:free"


def get_competition_models() -> list[tuple[str, str]]:
    """Return [(slot_label, model_name), ...] with exactly 3 unique slots."""
    third = os.getenv("OPENROUTER_MODEL") or FALLBACK_THIRD_MODEL
    candidates = list(DEFAULT_COMPETITION_MODELS)
    if third and third not in candidates:
        candidates.append(third)
    else:
        if FALLBACK_THIRD_MODEL not in candidates:
            candidates.append(FALLBACK_THIRD_MODEL)
        else:
            candidates.append("meta-llama/llama-3.3-70b-instruct:free")
    seen: list[str] = []
    for m in candidates:
        if m and m not in seen:
            seen.append(m)
        if len(seen) == 3:
            break
    while len(seen) < 3:
        seen.append(f"slot-{len(seen) + 1}-unset")
    slots = [("Model A", seen[0]), ("Model B", seen[1]), ("Model C", seen[2])]
    return slots


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _build_combined_messages(
    snapshot: dict,
    horizons: list[tuple[str, str, int]],
    performance_summary: str,
    model_self_summary: str = "",
    model_asset_summary: str = "",
    asset_summary: str = "",
) -> list[dict]:
    """Build a concise prompt for a single combined forecast request.

    Demands very compact JSON with short rationales to minimize the chance
    of token-truncation mid-response. Includes asset snapshot, horizons,
    and feedback streams (overall, model-self, model-on-asset, asset).
    """
    system = (
        "You are a crypto forecasting assistant. Reply with ONE compact JSON "
        "object only (no markdown, no commentary, no code fences, no whitespace "
        "beyond what JSON requires). Schema EXACTLY: "
        '{"forecasts":{"5m":F,"30m":F,"6h":F}} where '
        'F={"direction":"up"|"down","predicted_change":<float percent>,'
        '"confidence":<float 0..1>,"rationale":"<=60 chars, no quotes/newlines"}. '
        "Keep the entire response under 700 characters. "
        "Calibrate confidence using the supplied performance feedback."
    )
    user = (
        f"Asset: {snapshot['symbol']} ({snapshot['name']})\n"
        f"Price: ${snapshot['price']:.6f} | 24h: {snapshot['change_24h']:.2f}% | "
        f"Vol: ${snapshot['volume_24h']:,.0f} | Src: {snapshot['source']} | "
        f"Time: {snapshot['timestamp']}\n"
        f"Horizons: 5m (5min), 30m (30min), 6h (360min).\n"
        f"Overall recent performance: {performance_summary}\n"
        f"Your model's recent accuracy: {model_self_summary or 'none yet'}\n"
        f"Your model on {snapshot['symbol']}: {model_asset_summary or 'none yet'}\n"
        f"{snapshot['symbol']} recent outcomes (all models): {asset_summary or 'none yet'}\n"
        'Return ONLY compact JSON: {"forecasts":{"5m":{...},"30m":{...},"6h":{...}}}'
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _build_repair_messages(
    snapshot: dict,
    horizons: list[tuple[str, str, int]],
    prior_content: str,
    parse_error: str,
) -> list[dict]:
    """Stricter repair/compact retry prompt when first attempt failed parsing."""
    system = (
        "You output ONLY a single compact JSON object. No prose, no markdown, "
        "no code fences, no trailing text. Rationale strings must be <=40 "
        "characters and contain no double quotes or newlines. The response "
        "MUST be under 600 characters total. "
        'Schema EXACTLY: {"forecasts":{"5m":F,"30m":F,"6h":F}} where '
        'F={"direction":"up"|"down","predicted_change":<float>,'
        '"confidence":<float 0..1>,"rationale":"<=40 chars"}.'
    )
    safe_prior = (prior_content or "")[:400].replace("`", "'")
    user = (
        f"Previous response failed JSON parsing ({parse_error[:120]}). "
        f"Re-emit the forecast for {snapshot['symbol']} (price "
        f"${snapshot['price']:.6f}, 24h {snapshot['change_24h']:.2f}%) at "
        "horizons 5m, 30m, 6h as ONE compact JSON object matching the schema. "
        f"Previous (broken) output snippet: {safe_prior}\n"
        'Return ONLY: {"forecasts":{"5m":{...},"30m":{...},"6h":{...}}}'
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _extract_json_object(content: str) -> str:
    """Extract the first balanced JSON object substring from content.

    Handles cases where the model wraps JSON in code fences, prefixes prose,
    or appends trailing text after the JSON object. Returns the substring
    starting at the first `{` whose matching `}` closes the top-level object.
    Raises ValueError if no balanced object can be found.
    """
    if not content:
        raise ValueError("empty content")
    text = content.strip()
    # Strip code fences if present (fix empty string startswith bug)
    if text.startswith(""):
        lines = text.split("\n")
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith(""):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    if start == -1:
        raise ValueError("no '{' found in content")
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("unbalanced braces (likely truncated)")


class SuppressParserLogging:
    """Context manager to temporarily suppress handled/expected parser logging on stderr."""

    def __enter__(self):
        self.logger = logging.getLogger()
        self.old_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.CRITICAL + 1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


def _parse_forecast_json(content: str) -> dict:
    """Parse model content into a dict, with robust extraction fallback."""
    if not content:
        raise RuntimeError("empty content")
    # Fast path - try direct parse quietly without logging errors
    with SuppressParserLogging():
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logging.exception("Unexpected error")
            logging.debug("Direct JSON loads failed, attempting extraction.")
    # Extract balanced JSON object substring
    extracted = _extract_json_object(content)
    with SuppressParserLogging():
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            # Last-ditch: drop trailing comma artifacts that some models emit
            cleaned = extracted.replace(",}", "}").replace(",]", "]")
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as je2:
                logging.exception("Unexpected error")
                raise RuntimeError(
                    f"Invalid JSON: {str(je2)[:120]} :: snippet={extracted[:200]}"
                ) from je2


class DashboardState(rx.State):
    active_nav: str = "Overview"
    nav_items: list[dict[str, str]] = [
        {"label": "Overview", "icon": "layout-dashboard"},
        {"label": "Forecasts", "icon": "line-chart"},
        {"label": "Performance", "icon": "trending-up"},
        {"label": "Configuration", "icon": "settings"},
    ]

    market_loading: bool = False
    market_error: str = ""
    market_assets: list[MarketAsset] = []
    last_refresh: str = ""
    auto_refresh_started: bool = False

    active_target: str = "BTC"
    forecast_cadence: str = "Hourly"
    cadence_options: list[str] = [
        "Every 15 minutes",
        "Every 30 minutes",
        "Hourly",
        "Every 6 hours",
    ]

    forecasts: list[ForecastWindow] = []
    predictions_loading: bool = False
    predictions_error: str = ""
    last_prediction_run: str = ""
    performance_records: list[PerformanceRecord] = []
    last_competition_results: list[CompetitionResult] = []
    competition_progress: str = ""
    scheduler_started: bool = False
    scheduler_status: str = "Idle"
    next_scheduled_run: str = ""
    next_scheduled_run_ts: float = 0.0
    last_scheduled_run: str = ""
    scheduled_runs_count: int = 0

    providers: list[ProviderStatus] = [
        {
            "name": "SoSoValue",
            "kind": "Market Data",
            "status": "disconnected",
            "latency_ms": 0,
            "last_check": "—",
            "message": "Awaiting first refresh",
        },
        {
            "name": "SoDEX",
            "kind": "Market Data",
            "status": "disconnected",
            "latency_ms": 0,
            "last_check": "—",
            "message": "Awaiting first refresh",
        },
        {
            "name": "LLM Router",
            "kind": "Prediction Model",
            "status": "disconnected",
            "latency_ms": 0,
            "last_check": "—",
            "message": "Awaiting first prediction run",
        },
    ]

    sodex_public: bool = True

    @rx.var
    def has_market_data(self) -> bool:
        return len(self.market_assets) > 0

    @rx.var
    def credentials_ready(self) -> bool:
        return bool(os.getenv("SOSOVALUE_API_KEY") or os.getenv("SOSO_API_KEY"))

    @rx.var
    def llm_router_ready(self) -> bool:
        return bool(os.getenv("OPENROUTER_API_KEY"))

    @rx.var
    def can_run_predictions(self) -> bool:
        return (
            self.llm_router_ready
            and len(self.market_assets) > 0
            and (not self.predictions_loading)
        )

    @rx.var
    def cadence_seconds(self) -> int:
        mapping = {
            "Every 15 minutes": 15 * 60,
            "Every 30 minutes": 30 * 60,
            "Hourly": 60 * 60,
            "Every 6 hours": 6 * 60 * 60,
        }
        return mapping.get(self.forecast_cadence, 60 * 60)

    @rx.var
    def scheduler_ready(self) -> bool:
        return (
            self.scheduler_started
            and self.llm_router_ready
            and len(self.market_assets) > 0
        )

    @rx.var
    def connected_count(self) -> int:
        return sum(1 for p in self.providers if p["status"] == "connected")

    @rx.var
    def total_providers(self) -> int:
        return len(self.providers)

    @rx.var
    def evaluated_count(self) -> int:
        return len(self.performance_records)

    @rx.var
    def directional_accuracy(self) -> float:
        if not self.performance_records:
            return 0.0
        correct = sum(1 for r in self.performance_records if r["correct"])
        return correct / len(self.performance_records) * 100.0

    @rx.var
    def avg_abs_error(self) -> float:
        if not self.performance_records:
            return 0.0
        return sum(r["abs_error"] for r in self.performance_records) / len(
            self.performance_records
        )

    @rx.var
    def pending_count(self) -> int:
        return sum(1 for f in self.forecasts if f["status"] == "pending")

    @rx.var
    def total_forecasts(self) -> int:
        return len(self.forecasts)

    @rx.var
    def unique_models(self) -> list[str]:
        seen: list[str] = []
        for f in self.forecasts:
            m = f["model"]
            if m and m not in seen:
                seen.append(m)
        return seen

    @rx.var
    def unique_model_slots(self) -> list[str]:
        seen: list[str] = []
        for f in self.forecasts:
            s = f.get("model_slot", "")
            if s and s not in seen:
                seen.append(s)
        return seen

    @rx.var
    def failed_count(self) -> int:
        return sum(1 for f in self.forecasts if f["status"] == "failed")

    @rx.var
    def model_leaderboard(self) -> list[ModelLeaderboardEntry]:
        if not self.forecasts:
            return []
        slot_groups: dict[str, list[ForecastWindow]] = {}
        slot_models: dict[str, str] = {}
        for f in self.forecasts:
            slot = f.get("model_slot", "")
            if not slot:
                continue
            slot_groups.setdefault(slot, []).append(f)
            if f.get("model"):
                slot_models[slot] = f["model"]
        out: list[ModelLeaderboardEntry] = []
        for slot, items in slot_groups.items():
            evaluated = [i for i in items if i["status"] == "evaluated"]
            pending = [i for i in items if i["status"] == "pending"]
            failed = [i for i in items if i["status"] == "failed"]
            success = [i for i in items if i["status"] != "failed"]
            ev_count = len(evaluated)
            correct = sum(1 for i in evaluated if i["correct"])
            dir_acc = correct / ev_count * 100.0 if ev_count > 0 else 0.0
            mae = (
                sum(i["abs_error"] for i in evaluated) / ev_count
                if ev_count > 0
                else 0.0
            )
            confs = [i["confidence"] for i in success if i["confidence"] > 0]
            avg_conf = sum(confs) / len(confs) if confs else 0.0
            by_asset: dict[str, list[ForecastWindow]] = {}
            for i in evaluated:
                by_asset.setdefault(i["target_symbol"], []).append(i)
            best_asset = ""
            best_acc = 0.0
            for sym, lst in by_asset.items():
                if not lst:
                    continue
                c = sum(1 for x in lst if x["correct"])
                a = c / len(lst) * 100.0
                if a > best_acc or (a == best_acc and best_asset == ""):
                    best_acc = a
                    best_asset = sym
            latest_ts = max(
                (i["generated_at_ts"] for i in items),
                default=0.0,
            )
            latest_label = ""
            for i in items:
                if i["generated_at_ts"] == latest_ts:
                    latest_label = i["generated_at"]
                    break
            if len(failed) == len(items) and len(items) > 0:
                status = "error"
            elif len(failed) > 0:
                status = "degraded"
            else:
                status = "healthy"
            out.append(
                {
                    "model_slot": slot,
                    "model": slot_models.get(slot, ""),
                    "evaluated": ev_count,
                    "pending": len(pending),
                    "failed": len(failed),
                    "success": len(success),
                    "total": len(items),
                    "directional_accuracy": dir_acc,
                    "avg_abs_error": mae,
                    "avg_confidence": avg_conf,
                    "best_asset": best_asset,
                    "best_asset_accuracy": best_acc,
                    "latest_run": latest_label,
                    "latest_run_ts": latest_ts,
                    "status": status,
                }
            )
        out.sort(
            key=lambda r: (
                -r["evaluated"],
                -r["directional_accuracy"],
                r["avg_abs_error"],
            )
        )
        return out

    @rx.var
    def competition_model_slots(self) -> list[dict[str, str]]:
        return [
            {"slot": label, "model": model}
            for label, model in get_competition_models()
        ]

    @rx.var
    def competition_asset_count(self) -> int:
        return sum(1 for a in self.market_assets if a["price"] > 0)

    @rx.var
    def competition_total_calls(self) -> int:
        return self.competition_asset_count * 3

    @rx.var
    async def filtered_forecasts(self) -> list[ForecastWindow]:
        from app.states.performance_state import PerformanceState

        ps = await self.get_state(PerformanceState)
        out: list[ForecastWindow] = []
        for f in self.forecasts:
            if (
                ps.filter_asset != "All"
                and f["target_symbol"] != ps.filter_asset
            ):
                continue
            if ps.filter_horizon != "All" and f["horizon"] != ps.filter_horizon:
                continue
            if ps.filter_accuracy != "All":
                if ps.filter_accuracy == "Pending" and f["status"] != "pending":
                    continue
                if ps.filter_accuracy == "Failed" and f["status"] != "failed":
                    continue
                if ps.filter_accuracy == "Correct" and not (
                    f["status"] == "evaluated" and f["correct"]
                ):
                    continue
                if ps.filter_accuracy == "Miss" and not (
                    f["status"] == "evaluated" and not f["correct"]
                ):
                    continue
            if ps.filter_model != "All" and f["model"] != ps.filter_model:
                continue
            if (
                ps.filter_model_slot != "All"
                and f.get("model_slot", "") != ps.filter_model_slot
            ):
                continue
            out.append(f)
        out.sort(key=lambda x: x["generated_at_ts"], reverse=True)
        return out

    @rx.var
    async def filtered_count(self) -> int:
        return len(await self.filtered_forecasts)

    @rx.event
    def set_active_nav(self, label: str):
        self.active_nav = label

    @rx.event
    def set_active_target(self, symbol: str):
        self.active_target = symbol

    @rx.event
    def set_cadence(self, cadence: str):
        self.forecast_cadence = cadence

    def _summarize_records(
        self, records: list[PerformanceRecord], detail_count: int = 3
    ) -> str:
        if not records:
            return "none yet"
        correct = sum(1 for r in records if r["correct"])
        acc = correct / len(records) * 100.0
        avg_err = sum(r["abs_error"] for r in records) / len(records)
        recent = "; ".join(
            f"{r['symbol']}/{r['horizon']} pred {r['predicted_change']:+.2f}% act {r['actual_change']:+.2f}%"
            for r in records[-detail_count:]
        )
        return f"{len(records)} eval, {acc:.0f}% dir-acc, {avg_err:.2f}% mae. Recent: {recent}"

    def _performance_summary(self) -> str:
        return self._summarize_records(self.performance_records[-8:])

    def _model_self_summary(self, model_slot: str) -> str:
        recs = [
            r for r in self.performance_records if r["model_slot"] == model_slot
        ][-8:]
        return self._summarize_records(recs)

    def _model_asset_summary(self, model_slot: str, symbol: str) -> str:
        recs = [
            r
            for r in self.performance_records
            if r["model_slot"] == model_slot and r["symbol"] == symbol
        ][-6:]
        return self._summarize_records(recs)

    def _asset_summary(self, symbol: str) -> str:
        recs = [r for r in self.performance_records if r["symbol"] == symbol][
            -6:
        ]
        return self._summarize_records(recs)

    def _evaluate_matured(self):
        """Evaluate matured pending forecasts and append performance records.

        This routine is intentionally defensive about state mutation:
        - Reads existing forecasts/performance_records into local copies.
        - Builds fully fresh lists (no aliasing back to existing dict refs).
        - Always reassigns self.forecasts and self.performance_records at
          the end, ensuring Reflex's __setattr__ observes the change even
          when no in-place mutation occurred.
        - Leaves failed forecasts and not-yet-matured pending forecasts
          untouched in the rebuilt list.
        - Dedupes performance records by forecast id so repeated invocations
          never double-count an evaluation.
        """
        current_forecasts = list(self.forecasts)
        if not current_forecasts:
            return
        now_ts = datetime.now(timezone.utc).timestamp()
        prices = {
            a["symbol"]: a["price"]
            for a in self.market_assets
            if a["price"] > 0
        }
        existing_records = list(self.performance_records)
        existing_record_ids = {r["id"] for r in existing_records}
        new_forecasts: list[ForecastWindow] = []
        new_records: list[PerformanceRecord] = list(existing_records)
        for f in current_forecasts:
            # Preserve evaluated/failed/non-pending forecasts as-is (copied).
            if f["status"] != "pending":
                new_forecasts.append(dict(f))
                continue
            # Future-maturity forecasts remain pending, untouched.
            if now_ts < f["matures_at_ts"]:
                new_forecasts.append(dict(f))
                continue
            actual = prices.get(f["target_symbol"])
            if actual is None or actual <= 0 or f["snapshot_price"] <= 0:
                # No price available to score against — keep pending.
                new_forecasts.append(dict(f))
                continue
            actual_price = float(actual)
            actual_change = (
                (actual_price - f["snapshot_price"]) / f["snapshot_price"]
            ) * 100.0
            actual_dir = "up" if actual_change >= 0 else "down"
            correct = actual_dir == f["direction"]
            abs_err = abs(actual_change - f["predicted_change"])
            evaluated_forecast: ForecastWindow = dict(f)  # type: ignore[assignment]
            evaluated_forecast["status"] = "evaluated"
            evaluated_forecast["actual_price"] = actual_price
            evaluated_forecast["actual_change"] = float(actual_change)
            evaluated_forecast["correct"] = bool(correct)
            evaluated_forecast["abs_error"] = float(abs_err)
            new_forecasts.append(evaluated_forecast)
            if f["id"] not in existing_record_ids:
                new_records.append(
                    {
                        "id": f["id"],
                        "symbol": f["target_symbol"],
                        "horizon": f["horizon"],
                        "predicted_direction": f["direction"],
                        "predicted_change": f["predicted_change"],
                        "actual_change": float(actual_change),
                        "correct": bool(correct),
                        "abs_error": float(abs_err),
                        "confidence": f["confidence"],
                        "evaluated_at": _now_iso(),
                        "evaluated_at_ts": now_ts,
                        "model": f.get("model", ""),
                        "model_slot": f.get("model_slot", ""),
                    }
                )
                existing_record_ids.add(f["id"])
        # Always reassign both lists so Reflex observes the change reliably.
        self.forecasts = new_forecasts
        self.performance_records = new_records

    def _apply_provider_results(self, results, quotes):
        new_providers: list[ProviderStatus] = []
        for r in results:
            new_providers.append(
                {
                    "name": r["name"],
                    "kind": r["kind"],
                    "status": r["status"],
                    "latency_ms": r["latency_ms"],
                    "last_check": r["last_check"],
                    "message": r["message"],
                }
            )
        existing_llm = next(
            (p for p in self.providers if p["name"] == "LLM Router"), None
        )
        if existing_llm is None:
            existing_llm = {
                "name": "LLM Router",
                "kind": "Prediction Model",
                "status": "connected" if openrouter_ready() else "disconnected",
                "latency_ms": 0,
                "last_check": "—",
                "message": (
                    f"Ready ({get_openrouter_model()})"
                    if openrouter_ready()
                    else "Missing OPENROUTER_API_KEY"
                ),
            }
        new_providers.append(existing_llm)
        self.providers = new_providers
        assets: list[MarketAsset] = []
        for q in quotes:
            assets.append(
                {
                    "symbol": q["symbol"],
                    "name": q["name"],
                    "price": q["price"],
                    "change_24h": q["change_24h"],
                    "volume_24h": q["volume_24h"],
                    "market_cap": q["market_cap"],
                    "source": q["source"],
                    "timestamp": q["timestamp"],
                }
            )
        self.market_assets = assets
        self.last_refresh = _now_iso()
        self._evaluate_matured()

    @rx.event(background=True)
    async def refresh_market_data(self):
        async with self:
            if self.market_loading:
                return
            self.market_loading = True
            self.market_error = ""
        try:
            results = await asyncio.to_thread(fetch_all_providers)
            quotes = merge_quotes(results)
        except Exception as e:
            logging.exception(f"refresh_market_data: {e}")
            async with self:
                self.market_loading = False
                self.market_error = (
                    f"Refresh failed: {type(e).__name__}: {str(e)[:140]}"
                )
            return
        async with self:
            self._apply_provider_results(results, quotes)
            connected_market = [
                r
                for r in results
                if r["status"] == "connected" and r["kind"] == "Market Data"
            ]
            if not self.market_assets:
                errs = "; ".join(
                    f"{r['name']}: {r['message']}"
                    for r in results
                    if r["status"] != "connected"
                )
                self.market_error = (
                    errs or "No market data returned by providers."
                )
            elif not connected_market:
                self.market_error = "All providers errored; no live data."
            else:
                self.market_error = ""
            self.market_loading = False

    def _parse_forecasts_for_pair(
        self,
        snapshot: dict,
        slot_label: str,
        model_name: str,
        payload: dict,
    ) -> list[ForecastWindow]:
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("OpenRouter returned no choices")
        choice = choices[0]
        msg = choice.get("message") or {}
        content = msg.get("content") or ""
        if not content:
            raise RuntimeError("OpenRouter returned empty content")
        finish = str(choice.get("finish_reason", "")).lower()
        native_finish = str(choice.get("native_finish_reason", "")).lower()
        truncated = (
            "length" in finish
            or "max_tokens" in finish
            or "length" in native_finish
            or "max_tokens" in native_finish
        )
        with SuppressParserLogging():
            try:
                parsed = _parse_forecast_json(content)
            except Exception as je:
                logging.exception("Unexpected error")
                tail = content[-80:] if content else ""
                trunc_note = (
                    " (response truncated by token limit)" if truncated else ""
                )
                raise RuntimeError(
                    f"Invalid JSON from model{trunc_note}: {str(je)[:160]} | tail={tail!r}"
                ) from je
        forecasts_obj = parsed.get("forecasts")
        if not isinstance(forecasts_obj, dict):
            if all(h_id in parsed for h_id, _, _ in HORIZONS):
                forecasts_obj = {h_id: parsed[h_id] for h_id, _, _ in HORIZONS}
            else:
                raise RuntimeError(
                    f'Missing "forecasts" object in response: {content[:200]}'
                )
        reasoning_details = msg.get("reasoning_details")
        latency_ms = int(payload.get("_latency_ms", 0))
        response_meta = {
            "id": payload.get("id", ""),
            "model": payload.get("model", ""),
            "provider": payload.get("provider", ""),
            "finish_reason": choice.get("finish_reason", ""),
            "native_finish_reason": choice.get("native_finish_reason", ""),
            "usage": payload.get("usage", {}),
            "latency_ms": latency_ms,
            "slot": slot_label,
            "requested_model": model_name,
        }
        response_meta_json = json.dumps(response_meta)
        reasoning_json = (
            json.dumps(reasoning_details) if reasoning_details else ""
        )
        out: list[ForecastWindow] = []
        for h_id, h_label, h_min in HORIZONS:
            entry = forecasts_obj.get(h_id)
            if not isinstance(entry, dict):
                raise RuntimeError(f'Missing forecast object for "{h_id}"')
            direction = str(entry.get("direction", "")).strip().lower()
            if direction not in ("up", "down"):
                raise RuntimeError(
                    f"Invalid direction for {h_id}: {direction!r}"
                )
            try:
                predicted_change = float(entry.get("predicted_change", 0.0))
            except (TypeError, ValueError) as e:
                raise RuntimeError(
                    f"predicted_change must be a number for {h_id}"
                ) from e
            try:
                confidence = float(entry.get("confidence", 0.0))
            except (TypeError, ValueError) as e:
                raise RuntimeError(
                    f"confidence must be a number for {h_id}"
                ) from e
            confidence = max(0.0, min(1.0, confidence))
            rationale = str(entry.get("rationale", "")).strip()
            now = datetime.now(timezone.utc)
            matures = now + timedelta(minutes=h_min)
            out.append(
                {
                    "id": str(uuid.uuid4()),
                    "horizon": h_id,
                    "label": h_label,
                    "horizon_minutes": h_min,
                    "target_symbol": snapshot["symbol"],
                    "snapshot_price": float(snapshot["price"]),
                    "snapshot_change_24h": float(snapshot["change_24h"]),
                    "predicted_change": predicted_change,
                    "confidence": confidence,
                    "direction": direction,
                    "rationale": rationale,
                    "generated_at": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "generated_at_ts": now.timestamp(),
                    "matures_at": matures.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "matures_at_ts": matures.timestamp(),
                    "status": "pending",
                    "actual_price": 0.0,
                    "actual_change": 0.0,
                    "correct": False,
                    "abs_error": 0.0,
                    "model": str(payload.get("model", model_name)),
                    "model_slot": slot_label,
                    "response_id": str(payload.get("id", "")),
                    "has_reasoning": bool(reasoning_details),
                    "prompt_context": "",
                    "reasoning_details": reasoning_json,
                    "response_metadata": response_meta_json,
                    "latency_ms": latency_ms,
                    "error": "",
                }
            )
        return out

    @rx.event(background=True)
    async def run_competition(self):
        async with self:
            if self.predictions_loading:
                return
            if not self.llm_router_ready:
                self.predictions_error = (
                    "OpenRouter is not configured (set OPENROUTER_API_KEY)."
                )
                return
            if not self.market_assets:
                self.predictions_error = (
                    "Market data unavailable — refresh markets before running."
                )
                return
            snapshots = [dict(a) for a in self.market_assets if a["price"] > 0]
            if not snapshots:
                self.predictions_error = "No valid market snapshots."
                return
            self.predictions_loading = True
            self.predictions_error = ""
            self.last_competition_results = []
            self.competition_progress = "Starting competition…"
            performance_summary = self._performance_summary()
            slots = get_competition_models()
            model_self_summaries = {
                label: self._model_self_summary(label) for label, _ in slots
            }
            asset_summaries = {
                snap["symbol"]: self._asset_summary(snap["symbol"])
                for snap in snapshots
            }
            model_asset_summaries = {
                (label, snap["symbol"]): self._model_asset_summary(
                    label, snap["symbol"]
                )
                for label, _ in slots
                for snap in snapshots
            }

        @rx.event
        async def run_one(
            snapshot: dict, slot_label: str, model_name: str
        ) -> tuple[str, str, dict, list[ForecastWindow] | None, str, int]:
            messages = _build_combined_messages(
                snapshot,
                HORIZONS,
                performance_summary,
                model_self_summary=model_self_summaries.get(slot_label, ""),
                model_asset_summary=model_asset_summaries.get(
                    (slot_label, snapshot["symbol"]), ""
                ),
                asset_summary=asset_summaries.get(snapshot["symbol"], ""),
            )
            first_error = ""
            first_payload_content = ""
            try:
                payload = await asyncio.to_thread(
                    call_openrouter, messages, 60, 0.2, 1400, model_name
                )
                latency = int(payload.get("_latency_ms", 0))
                forecasts = self._parse_forecasts_for_pair(
                    snapshot, slot_label, model_name, payload
                )
                prompt_json = json.dumps(messages)
                for f in forecasts:
                    f["prompt_context"] = prompt_json
                return (
                    slot_label,
                    model_name,
                    snapshot,
                    forecasts,
                    "",
                    latency,
                )
            except Exception as e:
                first_error = f"{type(e).__name__}: {str(e)[:180]}"
                with SuppressParserLogging():
                    try:
                        if "payload" in locals():
                            ch = (payload.get("choices") or [{}])[0]
                            first_payload_content = (
                                ch.get("message") or {}
                            ).get("content", "") or ""
                    except Exception:
                        logging.exception("Unexpected error")
                        first_payload_content = ""
                logging.warning(
                    f"run_competition first attempt failed (will retry with repair) slot={slot_label} model={model_name} sym={snapshot['symbol']}: {first_error}"
                )
            try:
                repair_messages = _build_repair_messages(
                    snapshot, HORIZONS, first_payload_content, first_error
                )
                payload2 = await asyncio.to_thread(
                    call_openrouter, repair_messages, 60, 0.1, 1400, model_name
                )
                latency2 = int(payload2.get("_latency_ms", 0))
                forecasts2 = self._parse_forecasts_for_pair(
                    snapshot, slot_label, model_name, payload2
                )
                prompt_json = json.dumps(repair_messages)
                for f in forecasts2:
                    f["prompt_context"] = prompt_json
                return (
                    slot_label,
                    model_name,
                    snapshot,
                    forecasts2,
                    "",
                    latency2,
                )
            except Exception as e2:
                logging.exception(
                    f"run_competition repair retry failed slot={slot_label} model={model_name} sym={snapshot['symbol']}: {e2}"
                )
                combined_err = f"{first_error} | repair: {type(e2).__name__}: {str(e2)[:140]}"
                return (slot_label, model_name, snapshot, None, combined_err, 0)

        tasks = [
            run_one(snap, slot, m) for snap in snapshots for slot, m in slots
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        async with self:
            new_forecasts: list[ForecastWindow] = []
            comp_results: list[CompetitionResult] = []
            success_count = 0
            error_count = 0
            for (
                slot_label,
                model_name,
                snap,
                forecasts,
                err,
                latency,
            ) in results:
                if forecasts:
                    new_forecasts.extend(forecasts)
                    success_count += 1
                    comp_results.append(
                        {
                            "model_slot": slot_label,
                            "model": model_name,
                            "symbol": snap["symbol"],
                            "status": "success",
                            "error": "",
                            "forecasts_count": len(forecasts),
                            "latency_ms": latency,
                        }
                    )
                else:
                    error_count += 1
                    # error placeholder (3 horizon stub records, status='failed')
                    now = datetime.now(timezone.utc)
                    for h_id, h_label, h_min in HORIZONS:
                        new_forecasts.append(
                            {
                                "id": str(uuid.uuid4()),
                                "horizon": h_id,
                                "label": h_label,
                                "horizon_minutes": h_min,
                                "target_symbol": snap["symbol"],
                                "snapshot_price": float(snap["price"]),
                                "snapshot_change_24h": float(
                                    snap["change_24h"]
                                ),
                                "predicted_change": 0.0,
                                "confidence": 0.0,
                                "direction": "up",
                                "rationale": "",
                                "generated_at": now.strftime(
                                    "%Y-%m-%d %H:%M:%S UTC"
                                ),
                                "generated_at_ts": now.timestamp(),
                                "matures_at": (
                                    now + timedelta(minutes=h_min)
                                ).strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "matures_at_ts": (
                                    now + timedelta(minutes=h_min)
                                ).timestamp(),
                                "status": "failed",
                                "actual_price": 0.0,
                                "actual_change": 0.0,
                                "correct": False,
                                "abs_error": 0.0,
                                "model": model_name,
                                "model_slot": slot_label,
                                "response_id": "",
                                "has_reasoning": False,
                                "prompt_context": "",
                                "reasoning_details": "",
                                "response_metadata": "",
                                "latency_ms": 0,
                                "error": err,
                            }
                        )
                    comp_results.append(
                        {
                            "model_slot": slot_label,
                            "model": model_name,
                            "symbol": snap["symbol"],
                            "status": "error",
                            "error": err,
                            "forecasts_count": 0,
                            "latency_ms": 0,
                        }
                    )

            # Replace prior forecasts for the (symbol, slot, horizon) triples we just generated
            replaced_keys = {
                (f["target_symbol"], f["model_slot"], f["horizon"])
                for f in new_forecasts
            }
            kept = [
                f
                for f in self.forecasts
                if (
                    f["target_symbol"],
                    f.get("model_slot", ""),
                    f["horizon"],
                )
                not in replaced_keys
            ]
            self.forecasts = kept + new_forecasts
            self.last_competition_results = comp_results
            self.last_prediction_run = _now_iso()
            self.predictions_loading = False
            if error_count > 0 and success_count == 0:
                self.predictions_error = (
                    f"All {error_count} model/asset calls failed. "
                    f"See competition results panel for details."
                )
            elif error_count > 0:
                self.predictions_error = (
                    f"{error_count} of {error_count + success_count} "
                    f"model/asset calls failed (see results panel)."
                )
            else:
                self.predictions_error = ""
            self.providers = [
                (
                    {
                        **p,
                        "status": (
                            "connected" if success_count > 0 else "error"
                        ),
                        "last_check": _now_iso(),
                        "message": (
                            f"{success_count} ok / {error_count} err across "
                            f"{len(slots)} models × {len(snapshots)} assets"
                        ),
                    }
                    if p["name"] == "LLM Router"
                    else p
                )
                for p in self.providers
            ]
            self.competition_progress = ""

    @rx.event
    def attempt_prediction_run(self):
        if not self.llm_router_ready:
            return rx.toast(
                title="OpenRouter not configured",
                description="Set OPENROUTER_API_KEY to enable predictions.",
                duration=4000,
            )
        if not self.market_assets:
            return rx.toast(
                title="No market data",
                description="Refresh markets before running the competition.",
                duration=4000,
            )
        return DashboardState.run_competition

    @rx.event(background=True)
    async def start_auto_refresh(self):
        async with self:
            if self.auto_refresh_started:
                return
            self.auto_refresh_started = True
        try:
            results = await asyncio.to_thread(fetch_all_providers)
            quotes = merge_quotes(results)
            async with self:
                self._apply_provider_results(results, quotes)
        except Exception as e:
            logging.exception(f"initial auto refresh: {e}")
        # Kick off scheduled competition runs alongside hourly market refresh.
        async with self:
            should_start_scheduler = not self.scheduler_started
        if should_start_scheduler:
            yield DashboardState.start_scheduled_competitions
        while True:
            try:
                await asyncio.sleep(3600)
                results = await asyncio.to_thread(fetch_all_providers)
                quotes = merge_quotes(results)
                async with self:
                    self._apply_provider_results(results, quotes)
            except Exception as e:
                logging.exception(f"hourly refresh: {e}")
                await asyncio.sleep(60)

    @rx.event(background=True)
    async def start_scheduled_competitions(self):
        async with self:
            if self.scheduler_started:
                return
            self.scheduler_started = True
            self.scheduler_status = "Waiting for readiness"
        while True:
            try:
                async with self:
                    interval = self.cadence_seconds
                    next_ts = datetime.now(timezone.utc).timestamp() + interval
                    self.next_scheduled_run_ts = next_ts
                    self.next_scheduled_run = datetime.fromtimestamp(
                        next_ts, tz=timezone.utc
                    ).strftime("%Y-%m-%d %H:%M:%S UTC")
                    self.scheduler_status = f"Next run in ~{interval // 60} min"
                await asyncio.sleep(interval)
                # Refresh markets first
                async with self:
                    self.scheduler_status = "Refreshing markets…"
                try:
                    results = await asyncio.to_thread(fetch_all_providers)
                    quotes = merge_quotes(results)
                    async with self:
                        self._apply_provider_results(results, quotes)
                except Exception as e:
                    logging.exception(f"scheduled refresh: {e}")
                    async with self:
                        self.scheduler_status = (
                            f"Refresh failed: {type(e).__name__}"
                        )
                    continue
                # Pre-flight checks
                async with self:
                    ready = (
                        self.llm_router_ready and len(self.market_assets) > 0
                    )
                    busy = self.predictions_loading
                    if not ready:
                        self.scheduler_status = (
                            "Skipped: missing OpenRouter or market data"
                        )
                    elif busy:
                        self.scheduler_status = (
                            "Skipped: previous run still in progress"
                        )
                    else:
                        self.scheduler_status = "Running competition…"
                if not ready or busy:
                    continue
                # Trigger competition (background event chain)
                yield DashboardState.run_competition
                # Mark scheduled run completion (best-effort timestamp)
                async with self:
                    self.last_scheduled_run = _now_iso()
                    self.scheduled_runs_count += 1
                    self.scheduler_status = "Run dispatched"
            except Exception as e:
                logging.exception(f"scheduler loop: {e}")
                async with self:
                    self.scheduler_status = f"Loop error: {type(e).__name__}"
                await asyncio.sleep(60)