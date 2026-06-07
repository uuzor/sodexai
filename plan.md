# Crypto Price Prediction Dashboard Plan

## Phase 1: Dashboard Experience and Configuration Foundation ✅
- [x] Establish a clean modern UI direction: light sidebar, blue accent, white bordered cards on a gray-50 background, compact data-dense layout, strong typography, and responsive behavior.
- [x] Build the main dashboard layout with header, sidebar navigation, current market summary, forecast window cards, and status indicators.
- [x] Add a configuration section for API credential status, active prediction target selection, forecast cadence controls, and safe validation messaging.
- [x] Create realistic empty, loading, success, and error states for market data, predictions, and configuration workflows.

## Phase 2: Market Data Ingestion and Scheduled Operations ✅
- [x] Validate external data provider access requirements for SoSoValue and SoDEX before implementing live ingestion.
- [x] Implement hourly market data refresh orchestration with provider health tracking and failure logging.
- [x] Normalize incoming market fields into a consistent structure for current price, volume, timestamp, and source attribution.
- [x] Connect refreshed market data to dashboard price cards, history charts, and prediction target context.

## Phase 3: Prediction Engine and Feedback Loop ✅
- [x] Validate the LLM routing service credentials and request format before implementing live prediction generation.
- [x] Generate structured forecasts every hour for 5-minute, 30-minute, and 6-hour horizons for the selected cryptocurrency.
- [x] Store each prediction with prompt context, market snapshot, forecast horizon, confidence, and generated rationale.
- [x] Compare mature predictions against subsequent actual market data and calculate directional accuracy and error metrics.
- [x] Feed recent performance history back into subsequent prediction context to refine future outputs.

## Phase 4: Model Performance and Operational Monitoring ✅
- [x] Build a model performance table with historical predictions, actual outcomes, accuracy status, confidence, and timestamps.
- [x] Add filtering by target asset, horizon, source, accuracy status, and date range.
- [x] Add summary metrics for directional accuracy, average error, provider uptime, and latest model run status.
- [x] Provide manual refresh and safe retry actions with clear user feedback and disabled states when credentials are missing.

## Phase 5: Multi-Model Multi-Asset Prediction Ground ✅
- [x] Expand prediction generation so three configured AI models compete each hour across four crypto assets.
- [x] Store model, asset, horizon, forecast, confidence, rationale, prompt context, response metadata, and generation status for every model run.
- [x] Keep the UI direction consistent: light sidebar, blue accent, white bordered cards on gray-50 background, compact model-comparison layout.
- [x] Add safe handling for per-model failures without blocking successful model predictions.

## Phase 6: Competition Scoring and Leaderboards ✅
- [x] Score matured predictions for every model and asset using actual subsequent market prices.
- [x] Calculate leaderboard metrics including directional accuracy, average absolute error, evaluated count, pending count, and model availability.
- [x] Feed recent model-specific and asset-specific performance back into future prediction prompts.
- [x] Add filtering by model, asset, horizon, accuracy status, and pending/evaluated status.

## Phase 7: Frontend Competition Experience and Readiness ✅
- [x] Build competition overview cards, model leaderboards, per-asset model forecast grids, and a detailed prediction log.
- [x] Add manual “Run Competition” and refresh actions with loading, disabled, empty, success, and error states.
- [x] Test real provider access, real OpenRouter model responses, scoring logic, filters, and manual actions.
- [x] Confirm scheduled hourly workflows update all model and asset views consistently.

## Phase 8: Backend Model Reliability and Competition Automation ✅
- [x] Replace the unavailable third competition model with the requested free model.
- [x] Validate that the requested model is reachable through the live routing service.
- [x] Automate scheduled competition runs using the configured cadence while preventing overlapping runs.
- [x] Surface scheduled-run readiness, status, and timing clearly in the dashboard.
- [x] Test manual and scheduled competition paths with real provider-backed state.