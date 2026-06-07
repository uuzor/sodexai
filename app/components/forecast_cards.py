import reflex as rx
from app.states.dashboard_state import DashboardState, ForecastWindow


def _status_pill(forecast: ForecastWindow) -> rx.Component:
    return rx.match(
        forecast["status"],
        (
            "evaluated",
            rx.cond(
                forecast["correct"],
                rx.el.div(
                    rx.icon("check", class_name="h-3 w-3 text-emerald-700"),
                    rx.el.span(
                        "Correct",
                        class_name="text-[10px] font-semibold text-emerald-700",
                    ),
                    class_name="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-emerald-50 border border-emerald-100",
                ),
                rx.el.div(
                    rx.icon("x", class_name="h-3 w-3 text-red-700"),
                    rx.el.span(
                        "Miss",
                        class_name="text-[10px] font-semibold text-red-700",
                    ),
                    class_name="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-red-50 border border-red-100",
                ),
            ),
        ),
        (
            "failed",
            rx.el.div(
                rx.icon("circle-alert", class_name="h-3 w-3 text-red-700"),
                rx.el.span(
                    "Failed",
                    class_name="text-[10px] font-semibold text-red-700",
                ),
                class_name="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-red-50 border border-red-100",
            ),
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse"
            ),
            rx.el.span(
                "Pending",
                class_name="text-[10px] font-semibold text-amber-700",
            ),
            class_name="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-amber-50 border border-amber-100",
        ),
    )


def forecast_card(forecast: ForecastWindow) -> rx.Component:
    is_up = forecast["direction"] == "up"
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("clock", class_name="h-3.5 w-3.5 text-blue-600"),
                    rx.el.span(
                        forecast["label"],
                        class_name="text-xs font-semibold text-blue-700",
                    ),
                    class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-blue-50 border border-blue-100 w-fit",
                ),
                _status_pill(forecast),
                class_name="flex items-center justify-between mb-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            forecast["model_slot"],
                            class_name="text-[10px] font-bold text-purple-700 px-1.5 py-0.5 rounded bg-purple-50 border border-purple-100",
                        ),
                        rx.el.span(
                            f"For {forecast['target_symbol']}",
                            class_name="text-[11px] text-gray-500",
                        ),
                        class_name="flex items-center gap-1.5 mb-1",
                    ),
                    rx.el.div(
                        rx.cond(
                            is_up,
                            rx.icon(
                                "arrow-up-right",
                                class_name="h-5 w-5 text-emerald-600",
                            ),
                            rx.icon(
                                "arrow-down-right",
                                class_name="h-5 w-5 text-red-600",
                            ),
                        ),
                        rx.el.p(
                            rx.cond(
                                is_up,
                                f"+{forecast['predicted_change']:.2f}%",
                                f"{forecast['predicted_change']:.2f}%",
                            ),
                            class_name=rx.cond(
                                is_up,
                                "text-2xl font-bold text-emerald-600 tabular-nums",
                                "text-2xl font-bold text-red-600 tabular-nums",
                            ),
                        ),
                        class_name="flex items-center gap-1",
                    ),
                ),
                class_name="",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "Confidence", class_name="text-xs text-gray-500"
                    ),
                    rx.el.span(
                        f"{(forecast['confidence'] * 100):.0f}%",
                        class_name="text-xs font-semibold text-gray-700 tabular-nums",
                    ),
                    class_name="flex justify-between mb-1",
                ),
                rx.el.div(
                    rx.el.div(
                        class_name="h-full bg-blue-600 rounded-full",
                        style={"width": f"{forecast['confidence'] * 100}%"},
                    ),
                    class_name="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden",
                ),
                class_name="mt-4",
            ),
            rx.el.p(
                forecast["rationale"],
                class_name="text-xs text-gray-600 leading-relaxed mt-3 line-clamp-3",
            ),
            rx.cond(
                forecast["status"] == "evaluated",
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Actual",
                            class_name="text-[10px] text-gray-500 uppercase tracking-wider",
                        ),
                        rx.el.span(
                            rx.cond(
                                forecast["actual_change"] >= 0,
                                f"+{forecast['actual_change']:.2f}%",
                                f"{forecast['actual_change']:.2f}%",
                            ),
                            class_name=rx.cond(
                                forecast["actual_change"] >= 0,
                                "text-xs font-semibold text-emerald-600 tabular-nums",
                                "text-xs font-semibold text-red-600 tabular-nums",
                            ),
                        ),
                        class_name="flex items-center justify-between",
                    ),
                    rx.el.div(
                        rx.el.span(
                            "Abs Error",
                            class_name="text-[10px] text-gray-500 uppercase tracking-wider",
                        ),
                        rx.el.span(
                            f"{forecast['abs_error']:.2f}%",
                            class_name="text-xs font-semibold text-gray-700 tabular-nums",
                        ),
                        class_name="flex items-center justify-between",
                    ),
                    class_name="mt-3 pt-3 border-t border-gray-100 flex flex-col gap-1",
                ),
                rx.fragment(),
            ),
            rx.el.div(
                rx.el.span(
                    forecast["generated_at"],
                    class_name="text-[10px] text-gray-400",
                ),
                rx.cond(
                    forecast["has_reasoning"],
                    rx.el.div(
                        rx.icon("brain", class_name="h-3 w-3 text-purple-500"),
                        rx.el.span(
                            "reasoning",
                            class_name="text-[10px] text-purple-600 font-medium",
                        ),
                        class_name="flex items-center gap-1",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center justify-between mt-3 pt-3 border-t border-gray-100",
            ),
            class_name="p-4",
        ),
        class_name="rounded-xl bg-white border border-gray-200 hover:border-gray-300 transition-all",
    )


def _run_button() -> rx.Component:
    return rx.el.button(
        rx.cond(
            DashboardState.predictions_loading,
            rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
            rx.icon("trophy", class_name="h-3.5 w-3.5"),
        ),
        rx.el.span(
            rx.cond(
                DashboardState.predictions_loading,
                "Running Competition…",
                "Run Competition",
            ),
            class_name="text-xs font-semibold",
        ),
        on_click=DashboardState.attempt_prediction_run,
        disabled=~DashboardState.can_run_predictions,
        class_name=rx.cond(
            DashboardState.can_run_predictions,
            "flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white border border-blue-600 transition-colors",
            "flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200",
        ),
    )


def _disabled_reason() -> rx.Component:
    return rx.cond(
        ~DashboardState.llm_router_ready,
        rx.el.div(
            rx.icon("shield-alert", class_name="h-3.5 w-3.5 text-amber-600"),
            rx.el.span(
                "OpenRouter key missing",
                class_name="text-[11px] font-medium text-amber-700",
            ),
            class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-50 border border-amber-100",
        ),
        rx.cond(
            ~DashboardState.has_market_data,
            rx.el.div(
                rx.icon("cloud-off", class_name="h-3.5 w-3.5 text-amber-600"),
                rx.el.span(
                    "Refresh markets first",
                    class_name="text-[11px] font-medium text-amber-700",
                ),
                class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-50 border border-amber-100",
            ),
            rx.fragment(),
        ),
    )


def _empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.cond(
                DashboardState.llm_router_ready,
                rx.icon("trophy", class_name="h-5 w-5 text-blue-600"),
                rx.icon("lock", class_name="h-5 w-5 text-amber-600"),
            ),
            class_name=rx.cond(
                DashboardState.llm_router_ready,
                "h-10 w-10 rounded-full bg-blue-50 flex items-center justify-center mb-3",
                "h-10 w-10 rounded-full bg-amber-50 flex items-center justify-center mb-3",
            ),
        ),
        rx.cond(
            DashboardState.llm_router_ready,
            rx.el.p(
                "Ready to run the prediction competition",
                class_name="text-sm font-semibold text-gray-900 mb-1",
            ),
            rx.el.p(
                "OpenRouter is not configured",
                class_name="text-sm font-semibold text-gray-900 mb-1",
            ),
        ),
        rx.cond(
            DashboardState.llm_router_ready,
            rx.el.p(
                f"Click Run Competition to call 3 models on {DashboardState.competition_asset_count} assets across 5m / 30m / 6h horizons.",
                class_name="text-xs text-gray-500 max-w-md text-center",
            ),
            rx.el.p(
                "Set OPENROUTER_API_KEY (and optionally OPENROUTER_MODEL) to enable live prediction generation.",
                class_name="text-xs text-gray-500 max-w-md text-center",
            ),
        ),
        class_name="flex flex-col items-center justify-center py-12 rounded-xl bg-white border border-dashed border-gray-300",
    )


def _error_banner() -> rx.Component:
    return rx.cond(
        DashboardState.predictions_error != "",
        rx.el.div(
            rx.icon(
                "circle-alert",
                class_name="h-4 w-4 text-red-600 shrink-0 mt-0.5",
            ),
            rx.el.div(
                rx.el.p(
                    "Prediction failed",
                    class_name="text-xs font-semibold text-red-900",
                ),
                rx.el.p(
                    DashboardState.predictions_error,
                    class_name="text-[11px] text-red-700 break-all",
                ),
            ),
            class_name="flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-100 mb-3",
        ),
        rx.fragment(),
    )


def _model_slot_chip(slot: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            slot["slot"],
            class_name="text-[10px] font-bold text-purple-700",
        ),
        rx.el.span(
            slot["model"],
            class_name="text-[10px] font-mono text-gray-600 truncate",
        ),
        class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-white border border-gray-200 max-w-[280px]",
    )


def _competition_result_row(r) -> rx.Component:
    return rx.el.div(
        rx.cond(
            r["status"] == "success",
            rx.icon(
                "circle-check", class_name="h-3 w-3 text-emerald-600 shrink-0"
            ),
            rx.icon("circle-alert", class_name="h-3 w-3 text-red-600 shrink-0"),
        ),
        rx.el.span(
            r["model_slot"],
            class_name="text-[10px] font-bold text-purple-700",
        ),
        rx.el.span(
            r["symbol"],
            class_name="text-[10px] font-semibold text-gray-900",
        ),
        rx.el.span(
            rx.cond(
                r["status"] == "success",
                f"{r['forecasts_count']} forecasts · {r['latency_ms']}ms",
                r["error"],
            ),
            class_name=rx.cond(
                r["status"] == "success",
                "text-[10px] text-gray-500 truncate",
                "text-[10px] text-red-600 truncate",
            ),
        ),
        class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-50 border border-gray-200",
    )


def _competition_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("trophy", class_name="h-3.5 w-3.5 text-purple-600"),
                rx.el.span(
                    "Competition Slots",
                    class_name="text-[11px] font-semibold text-gray-900",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.span(
                f"{DashboardState.competition_asset_count} assets × 3 models × 3 horizons",
                class_name="text-[10px] text-gray-500",
            ),
            class_name="flex items-center justify-between mb-2",
        ),
        rx.el.div(
            rx.foreach(
                DashboardState.competition_model_slots, _model_slot_chip
            ),
            class_name="flex flex-wrap gap-1.5 mb-2",
        ),
        rx.cond(
            DashboardState.last_competition_results.length() > 0,
            rx.el.div(
                rx.el.p(
                    "Last run results",
                    class_name="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5",
                ),
                rx.el.div(
                    rx.foreach(
                        DashboardState.last_competition_results,
                        _competition_result_row,
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 gap-1.5",
                ),
            ),
            rx.fragment(),
        ),
        class_name="p-3 rounded-xl bg-white border border-gray-200 mb-4",
    )


def forecast_cards() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Prediction Competition",
                    class_name="text-base font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"3 models × {DashboardState.competition_asset_count} assets × 5m / 30m / 6h horizons — live OpenRouter forecasts",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.el.div(
                _disabled_reason(),
                rx.cond(
                    DashboardState.last_prediction_run != "",
                    rx.el.div(
                        rx.el.div(
                            class_name="h-1.5 w-1.5 rounded-full bg-emerald-500"
                        ),
                        rx.el.span(
                            f"Last run {DashboardState.last_prediction_run}",
                            class_name="text-[11px] text-gray-600 font-medium",
                        ),
                        class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-50 border border-gray-200",
                    ),
                    rx.fragment(),
                ),
                _run_button(),
                class_name="flex items-center gap-2 flex-wrap",
            ),
            class_name="flex items-center justify-between mb-4 gap-3 flex-wrap",
        ),
        _error_banner(),
        _competition_panel(),
        rx.cond(
            DashboardState.predictions_loading
            & (DashboardState.forecasts.length() == 0),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "loader-circle",
                        class_name="h-5 w-5 text-blue-600 animate-spin",
                    ),
                    class_name="h-10 w-10 rounded-full bg-blue-50 flex items-center justify-center mb-3",
                ),
                rx.el.p(
                    "Running competition across all models and assets…",
                    class_name="text-sm font-semibold text-gray-900 mb-1",
                ),
                rx.el.p(
                    "3 models × 4 assets × 3 horizons in parallel. This typically takes 10-30 seconds.",
                    class_name="text-xs text-gray-500 max-w-md text-center",
                ),
                class_name="flex flex-col items-center justify-center py-12 rounded-xl bg-white border border-dashed border-blue-200",
            ),
            rx.cond(
                DashboardState.forecasts.length() > 0,
                rx.el.div(
                    rx.foreach(DashboardState.forecasts, forecast_card),
                    class_name="grid grid-cols-1 md:grid-cols-3 gap-4",
                ),
                _empty_state(),
            ),
        ),
        rx.cond(
            DashboardState.evaluated_count > 0,
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "trending-up", class_name="h-3.5 w-3.5 text-blue-600"
                    ),
                    rx.el.span(
                        "Feedback loop",
                        class_name="text-[11px] font-semibold text-gray-700",
                    ),
                    class_name="flex items-center gap-1.5 mb-1",
                ),
                rx.el.p(
                    f"{DashboardState.evaluated_count} matured · {DashboardState.directional_accuracy:.0f}% directional accuracy · {DashboardState.avg_abs_error:.2f}% mean abs error",
                    class_name="text-[11px] text-gray-600",
                ),
                class_name="mt-3 p-3 rounded-lg bg-gray-50 border border-gray-200",
            ),
            rx.fragment(),
        ),
        class_name="mb-6",
    )