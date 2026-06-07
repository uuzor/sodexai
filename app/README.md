
# CryptoForecast — Multi-Model Crypto Prediction Competition Dashboard

> A live, transparent benchmark where multiple AI models compete head-to-head to forecast cryptocurrency price movements — scored against real subsequent market data.

---

## 🚀 What is CryptoForecast?

**CryptoForecast** is a production-grade dashboard that runs a continuous, hourly **AI prediction competition** over the world's most-traded crypto assets. It pulls live market data, dispatches structured forecasts to three competing language models, scores those forecasts against actual market outcomes, and surfaces the results in a clean, real-time leaderboard.

The platform is designed to answer one question with empirical rigor:

> **Which AI model is actually better at forecasting crypto price movements — and by how much?**

Rather than relying on cherry-picked anecdotes or backtests, CryptoForecast generates *forward-looking* predictions, locks them in, waits for the market to mature, and then scores them objectively. Every prediction, prompt, response, and outcome is logged.

---

## 🎯 Core Workflow


   ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
   │  1. Market Ingest    │ ─▶ │  2. Competition Run  │ ─▶ │  3. Score & Learn    │
   │  SoSoValue + SoDEX   │    │  3 Models × 4 Assets │    │  Match against live  │
   │  BTC ETH SOL AVAX    │    │  × 3 Horizons        │    │  prices, leaderboard │
   └──────────────────────┘    └──────────────────────┘    └──────────────────────┘
            ▲                                                          │
            └──────────────── feedback loop ───────────────────────────┘


### 1. Live Market Ingestion
- **Primary source:** [SoSoValue](https://sosovalue.com/) Open API — institutional-grade aggregated market snapshots (price, 24h change, volume, market cap).
- **Fallback / cross-source:** [SoDEX](https://testnet-gw.sodex.dev/) public testnet ticker feed — provides redundancy and per-symbol fallback when the primary provider is rate-limited.
- **Refresh cadence:** Automatic hourly polling, plus on-demand manual refresh from the dashboard header.
- **Resilience:** Per-provider health tracking, latency telemetry, exponential cooldown, and graceful per-asset fallback.

### 2. Multi-Model AI Competition
Every cadence tick, the engine dispatches a structured forecast request to **three competing models** running on [OpenRouter](https://openrouter.ai):

| Slot | Default Model | Role |
|------|---------------|------|
| **Model A** | `nvidia/nemotron-3-super-120b-a12b:free` | Heavyweight reasoning baseline |
| **Model B** | `openai/gpt-oss-120b:free` | Open-source frontier model |
| **Model C** | Configurable via `OPENROUTER_MODEL` | User-selected challenger |

For **each asset (BTC, ETH, SOL, AVAX)** and **each horizon (5m, 30m, 6h)**, every model produces a structured JSON forecast containing:
- `direction` — up / down
- `predicted_change` — % move
- `confidence` — 0..1 calibration
- `rationale` — short explanation

A run produces **3 models × 4 assets × 3 horizons = 36 forecasts**, all dispatched in parallel.

### 3. Scoring & Feedback Loop
- Each forecast is timestamped and locked with the snapshot price at generation time.
- When a horizon matures (e.g. 5 minutes later), the engine fetches the actual price.
- It computes:
  - **Directional accuracy** — did the model correctly call up vs. down?
  - **Absolute error** — `|predicted_change − actual_change|`
  - **Confidence calibration** — is high-confidence accuracy meaningfully higher?
- **Feedback enrichment:** Recent outcomes — overall, per-model, per-asset, and per-(model, asset) — are injected into subsequent prompts so models can self-calibrate.

---

## ✨ Core Features

### 📊 Real-Time Dashboard
- **Market Summary** — Live BTC / ETH / SOL / AVAX prices with 24h change, source attribution, and one-click target switching.
- **Forecast Windows** — Per-horizon prediction cards with direction, predicted %, confidence bar, rationale, and reasoning indicator.
- **Per-Asset Model Comparison Grid** — Side-by-side forecasts from every model across every horizon for each asset.
- **Model Leaderboard** — Live ranking by directional accuracy, mean absolute error, evaluated/pending/failed counts, best asset, and average confidence.
- **Performance Log** — Filterable table of every prediction ever generated, with full metadata (model, slot, horizon, prompt, response, latency).

### ⚙️ Operations & Reliability
- **Hourly Competition Readiness Panel** — At-a-glance check of credentials, market data freshness, OpenRouter availability, and competition status.
- **Provider Health** — Per-provider connection state, latency, and last-checked timestamps.
- **Scheduler** — Automatic hourly competition dispatch with overlap protection and cadence selector (15m / 30m / 1h / 6h).
- **Filters** — Slice the prediction log by asset, horizon, accuracy status, model, and slot.
- **Manual Controls** — On-demand market refresh and "Run Competition" actions with full disabled / loading / error states.

### 🛡️ Robustness
- Per-model failure isolation — one model crashing never blocks the others.
- Automatic JSON repair retry with stricter schema enforcement on parse failure.
- Token-budget tuning to avoid mid-response truncation.
- Defensive evaluation that never double-counts matured forecasts.

---

## 🏆 How Scoring & Leaderboards Work

### Per-Forecast Scoring
When a forecast matures:
1. Fetch the latest price for the target asset.
2. Compute `actual_change = (actual_price − snapshot_price) / snapshot_price × 100`.
3. Determine `actual_direction` (up if ≥ 0, else down).
4. Mark **correct** if `predicted_direction == actual_direction`.
5. Compute **abs_error** = `|predicted_change − actual_change|`.

### Per-Model Aggregation
Each model slot accumulates:
| Metric | Definition |
|---|---|
| **Directional Accuracy** | % of evaluated forecasts where direction was correct |
| **Mean Absolute Error** | Average `abs_error` across evaluated forecasts |
| **Avg Confidence** | Mean of `confidence` across all successful forecasts |
| **Best Asset** | Asset on which the model has highest directional accuracy |
| **Evaluated / Pending / Failed** | Lifecycle counters for transparency |
| **Status** | `healthy` / `degraded` / `error` based on failure ratio |

### Leaderboard Sort
Models are ranked by:
1. **Most evaluated** (sample size weight)
2. **Highest directional accuracy** (primary signal)
3. **Lowest mean absolute error** (precision tiebreaker)

This favors models that have actually been measured at scale, then rewards correctness, then precision.

---

## 🔧 Setup & Configuration (High Level)

CryptoForecast reads all credentials from **secure environment variables** — never from client state or version control.

| Variable | Required | Purpose |
|---|---|---|
| `SOSOVALUE_API_KEY` | Yes | Primary market data ingestion |
| `OPENROUTER_API_KEY` | Yes | AI model competition engine |
| `OPENROUTER_MODEL` | Optional | Override Model C with a custom OpenRouter model id |

> **SoDEX testnet** is a public endpoint and requires no key.

The dashboard's **Configuration** tab and **Hourly Competition Readiness** panel surface live credential status so operators always know exactly what is wired up — without ever displaying secret values.

### Cadence Selection
Choose from `Every 15 minutes`, `Every 30 minutes`, `Hourly` (default), or `Every 6 hours`. The scheduler protects against overlapping runs and skips ticks if the previous batch is still in flight.

### Active Prediction Target
The active asset (BTC / ETH / SOL / AVAX) is configurable from the Market Summary cards or the Configuration panel. Note that the competition still runs across **all four** assets every cadence — the active target merely highlights primary focus in the UI.

---

## 💼 Monetization Strategy

CryptoForecast is positioned to monetize across three tiers, each unlocking deeper access to the live competition signal:

### Tier 1 — Free Public Leaderboard
- Public-facing model rankings, sample forecasts, and historical accuracy summaries.
- Drives top-of-funnel awareness and SEO around "best AI for crypto prediction."
- Ad-supported and referral-monetized (exchange affiliate links, OpenRouter referrals).

### Tier 2 — Pro Subscription ($29–$99 / mo)
- Real-time access to **all** active forecasts across all models, assets, and horizons.
- Confidence-filtered alerting (e.g. "notify me when ≥2 models agree at >0.7 confidence").
- Custom model slot configuration (bring-your-own OpenRouter model).
- Exportable CSV / JSON of full prediction history.
- Webhook delivery into Discord / Telegram / Slack.

### Tier 3 — Enterprise & API ($499+ / mo)
- Programmatic API access to live forecasts and aggregated leaderboard signals.
- Custom asset universes (top-50, DeFi basket, narrative baskets).
- Dedicated model slots for proprietary fine-tuned models with private leaderboards.
- White-label dashboards for funds, market-makers, and research desks.
- SLA-backed uptime and priority OpenRouter routing.

### Adjacent Revenue Streams
- **OpenRouter referral fees** on all model inference passed through to user-funded slots.
- **Exchange affiliate partnerships** (one-click "trade this signal" links).
- **Sponsored model slots** — model providers can pay to run their model in the public leaderboard for visibility and benchmark credibility.
- **Research reports** — periodic published "State of AI Crypto Forecasting" reports leveraging proprietary leaderboard data.

---

## 👥 Target Users

| Persona | Why They Care |
|---|---|
| **Active crypto traders** | Want a calibrated AI signal layered on top of their own thesis |
| **Quant researchers** | Need a transparent, reproducible benchmark for LLM forecasting ability |
| **AI / ML engineers** | Evaluating frontier models on real-world structured prediction tasks |
| **Crypto funds & market-makers** | Looking for cheap signal and model-agreement indicators |
| **Model providers** | Want third-party validation of their model's forecasting capability |
| **Crypto-curious investors** | Want to understand "is AI actually any good at this?" before allocating |

---

## 🗺️ Roadmap

### ✅ Phases 1–8 — Foundation (Complete)
- [x] Modern, light-themed responsive dashboard UI.
- [x] Live SoSoValue + SoDEX market ingestion with provider health telemetry.
- [x] OpenRouter-powered three-model competition across BTC / ETH / SOL / AVAX.
- [x] 5m / 30m / 6h forecast horizons with structured JSON output and reasoning capture.
- [x] Automatic scoring against matured market prices.
- [x] Per-model leaderboard with directional accuracy, MAE, and best-asset analytics.
- [x] Filterable performance log and full prompt / response / metadata persistence.
- [x] Scheduled hourly competition with overlap protection and readiness gating.
- [x] Feedback loop injection (overall, per-model, per-asset, per-(model, asset)).

### 🚧 Phase 9 — Persistence & Public Surface
- [ ] Database-backed prediction history (Postgres) with multi-day retention.
- [ ] Public read-only leaderboard at root domain.
- [ ] Shareable model-vs-model and asset-vs-asset comparison pages.
- [ ] Historical accuracy charts (rolling 24h / 7d / 30d).

### 🔜 Phase 10 — User Accounts & Pro Tier
- [ ] OAuth-based sign-in (Google / GitHub).
- [ ] User-scoped custom model slots and watchlists.
- [ ] Pro subscription billing (Stripe).
- [ ] Webhook & email alerting on confidence-filtered events.

### 🔮 Phase 11 — Asset Universe Expansion
- [ ] Top-25 crypto coverage with configurable basket selection.
- [ ] Narrative baskets (AI tokens, DeFi, L1s, memecoins).
- [ ] On-chain signal augmentation (whale flows, exchange netflows).

### 🌐 Phase 12 — API & Enterprise
- [ ] Public REST + WebSocket forecast API.
- [ ] Rate-limited free tier + metered Pro / Enterprise tiers.
- [ ] White-label embeds and dashboard SDK.
- [ ] SOC 2 readiness and uptime SLA.

### 🧠 Phase 13 — Advanced Analytics
- [ ] Confidence-calibration curves (reliability diagrams).
- [ ] Model-agreement consensus signal as a meta-prediction.
- [ ] Regime detection (trend vs. mean-reverting market) and per-regime leaderboards.
- [ ] Quarterly published "State of AI Crypto Forecasting" report.

---

## ⚠️ Responsible Use & Financial Disclaimer

**CryptoForecast is a research and benchmarking tool, not financial advice.**

- All forecasts are generated by general-purpose language models without specialized financial training, real-time order-book context, or knowledge of your individual circumstances.
- Past directional accuracy is **not** indicative of future performance. A model with 70% historical accuracy can — and statistically will — produce extended losing streaks.
- Cryptocurrency markets are extraordinarily volatile. Prices can move significantly in seconds for reasons no model could anticipate (exchange outages, regulatory news, exploits, liquidations).
- The displayed confidence values are model self-reports and may be poorly calibrated.
- **Never trade based solely on a CryptoForecast signal.** Always combine with your own research, risk management, and, where appropriate, advice from a licensed financial professional.
- CryptoForecast and its operators accept **no liability** for trading decisions made on the basis of information shown in the dashboard.
- This product is **not** a registered investment advisor, broker-dealer, or fiduciary. No content here constitutes a recommendation to buy, sell, or hold any asset.

By using this dashboard you acknowledge these risks and accept full responsibility for any decisions you make.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend & State** | [Reflex](https://reflex.dev) (Python-native React) |
| **Styling** | Tailwind CSS, Inter typeface, light modern theme |
| **Market Data** | SoSoValue Open API + SoDEX testnet ticker feed |
| **AI Inference** | OpenRouter (multi-model routing) |
| **Scheduling** | Async background tasks with cadence-driven dispatch |
| **HTTP** | `requests` with strict timeouts and retry isolation |

---

## 📬 Contact & Contributing

CryptoForecast is in active development. For partnership inquiries, sponsored model slots, enterprise access, or collaboration on the upcoming public API, please reach out through the project's primary channel.

---

**Built with rigor. Evaluated against reality. Open to scrutiny.**

