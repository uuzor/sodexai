import reflex as rx
from app.states.dashboard_state import DashboardState, ForecastWindow
from app.states.performance_state import PerformanceState


def _metric_card(
    icon: str, label: str, value, sublabel: str, accent: str, bg: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name=f"h-4 w-4 {accent}"),
                class_name=f"h-9 w-9 rounded-lg {bg} border border-gray-200 flex items-center justify-center",
            ),
            rx.el.span(
                sublabel,
                class_name="text-[10px] font-semibold text-gray-400 tracking-wider",
            ),
            class_name="flex items-center justify-between mb-3",
        ),
        rx.el.p(label, class_name="text-xs text-gray-500 mb-1"),
        rx.el.p(
            value, class_name="text-xl font-bold text-gray-900 tabular-nums"
        ),
        class_name="p-4 rounded-xl bg-white border border-gray-200",
    )


def _summary_metrics() -> rx.Component:
    return rx.el.div(
        _metric_card(
            "target",
            "Directional Accuracy",
            f"{DashboardState.directional_accuracy:.1f}%",
            "EVALUATED",
            "text-emerald-600",
            "bg-emerald-50",
        ),
        _metric_card(
            "ruler",
            "Avg Absolute Error",
            f"{DashboardState.avg_abs_error:.2f}%",
            "MEAN",
            "text-blue-600",
            "bg-blue-50",
        ),
        _metric_card(
            "activity",
            "Provider Uptime",
            f"{DashboardState.connected_count}/{DashboardState.total_providers}",
            "CONNECTED",
            "text-purple-600",
            "bg-purple-50",
        ),
        _metric_card(
            "hourglass",
            "Pending Predictions",
            DashboardState.pending_count.to_string(),
            "MATURING",
            "text-amber-600",
            "bg-amber-50",
        ),
        _metric_card(
            "circle-check",
            "Evaluated Predictions",
            DashboardState.evaluated_count.to_string(),
            "SCORED",
            "text-emerald-600",
            "bg-emerald-50",
        ),
        _metric_card(
            "clock",
            "Last Model Run",
            rx.cond(
                DashboardState.last_prediction_run != "",
                DashboardState.last_prediction_run,
                "Never",
            ),
            "TIMESTAMP",
            "text-gray-600",
            "bg-gray-50",
        ),
        class_name="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4",
    )


def _filter_pill(label: str, active: bool, on_click) -> rx.Component:
    return rx.el.button(
        label,
        on_click=on_click,
        class_name=rx.cond(
            active,
            "px-2.5 py-1 rounded-md text-[11px] font-semibold bg-blue-600 text-white border border-blue-600 transition-colors",
            "px-2.5 py-1 rounded-md text-[11px] font-medium bg-white text-gray-700 border border-gray-200 hover:border-gray-300 transition-colors",
        ),
    )


def _asset_filter() -> rx.Component:
    options = ["All", "BTC", "ETH", "SOL", "AVAX"]
    return rx.el.div(
        rx.el.p(
            "Asset",
            class_name="text-[10px] font-semibold text-gray-400 tracking-wider mb-1.5",
        ),
        rx.el.div(
            rx.foreach(
                options,
                lambda o: _filter_pill(
                    o,
                    PerformanceState.filter_asset == o,
                    lambda: PerformanceState.set_filter_asset(o),
                ),
            ),
            class_name="flex flex-wrap gap-1.5",
        ),
    )


def _horizon_filter() -> rx.Component:
    options = ["All", "5m", "30m", "6h"]
    return rx.el.div(
        rx.el.p(
            "Horizon",
            class_name="text-[10px] font-semibold text-gray-400 tracking-wider mb-1.5",
        ),
        rx.el.div(
            rx.foreach(
                options,
                lambda o: _filter_pill(
                    o,
                    PerformanceState.filter_horizon == o,
                    lambda: PerformanceState.set_filter_horizon(o),
                ),
            ),
            class_name="flex flex-wrap gap-1.5",
        ),
    )


def _accuracy_filter() -> rx.Component:
    options = ["All", "Correct", "Miss", "Pending", "Failed"]
    return rx.el.div(
        rx.el.p(
            "Accuracy",
            class_name="text-[10px] font-semibold text-gray-400 tracking-wider mb-1.5",
        ),
        rx.el.div(
            rx.foreach(
                options,
                lambda o: _filter_pill(
                    o,
                    PerformanceState.filter_accuracy == o,
                    lambda: PerformanceState.set_filter_accuracy(o),
                ),
            ),
            class_name="flex flex-wrap gap-1.5",
        ),
    )


def _model_filter() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            "Model",
            class_name="text-[10px] font-semibold text-gray-400 tracking-wider mb-1.5",
        ),
        rx.el.div(
            _filter_pill(
                "All",
                PerformanceState.filter_model == "All",
                lambda: PerformanceState.set_filter_model("All"),
            ),
            rx.foreach(
                DashboardState.unique_models,
                lambda m: _filter_pill(
                    m,
                    PerformanceState.filter_model == m,
                    lambda: PerformanceState.set_filter_model(m),
                ),
            ),
            class_name="flex flex-wrap gap-1.5",
        ),
    )


def _model_slot_filter() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            "Slot",
            class_name="text-[10px] font-semibold text-gray-400 tracking-wider mb-1.5",
        ),
        rx.el.div(
            _filter_pill(
                "All",
                PerformanceState.filter_model_slot == "All",
                lambda: PerformanceState.set_filter_model_slot("All"),
            ),
            rx.foreach(
                DashboardState.unique_model_slots,
                lambda s: _filter_pill(
                    s,
                    PerformanceState.filter_model_slot == s,
                    lambda: PerformanceState.set_filter_model_slot(s),
                ),
            ),
            class_name="flex flex-wrap gap-1.5",
        ),
    )


def _filters_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("filter", class_name="h-3.5 w-3.5 text-gray-600"),
                rx.el.span(
                    "Filters",
                    class_name="text-xs font-semibold text-gray-900",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-3 w-3"),
                rx.el.span("Reset", class_name="text-[11px] font-medium"),
                on_click=PerformanceState.reset_filters,
                class_name="flex items-center gap-1 px-2 py-1 rounded-md text-gray-600 hover:bg-gray-100 transition-colors",
            ),
            class_name="flex items-center justify-between mb-3",
        ),
        rx.el.div(
            _asset_filter(),
            _horizon_filter(),
            _accuracy_filter(),
            _model_slot_filter(),
            _model_filter(),
            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
        ),
        class_name="p-4 rounded-xl bg-white border border-gray-200 mb-4",
    )


def _status_badge(forecast: ForecastWindow) -> rx.Component:
    return rx.cond(
        forecast["status"] == "evaluated",
        rx.cond(
            forecast["correct"],
            rx.el.div(
                rx.icon("check", class_name="h-3 w-3 text-emerald-700"),
                rx.el.span(
                    "Correct",
                    class_name="text-[10px] font-semibold text-emerald-700",
                ),
                class_name="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-emerald-50 border border-emerald-100 w-fit",
            ),
            rx.el.div(
                rx.icon("x", class_name="h-3 w-3 text-red-700"),
                rx.el.span(
                    "Miss",
                    class_name="text-[10px] font-semibold text-red-700",
                ),
                class_name="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-red-50 border border-red-100 w-fit",
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
            class_name="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-amber-50 border border-amber-100 w-fit",
        ),
    )


def _direction_cell(forecast: ForecastWindow) -> rx.Component:
    is_up = forecast["direction"] == "up"
    return rx.el.div(
        rx.cond(
            is_up,
            rx.icon(
                "arrow-up-right", class_name="h-3.5 w-3.5 text-emerald-600"
            ),
            rx.icon("arrow-down-right", class_name="h-3.5 w-3.5 text-red-600"),
        ),
        rx.el.span(
            rx.cond(
                is_up,
                f"+{forecast['predicted_change']:.2f}%",
                f"{forecast['predicted_change']:.2f}%",
            ),
            class_name=rx.cond(
                is_up,
                "text-xs font-semibold text-emerald-600 tabular-nums",
                "text-xs font-semibold text-red-600 tabular-nums",
            ),
        ),
        class_name="flex items-center gap-1",
    )


def _actual_cell(forecast: ForecastWindow) -> rx.Component:
    return rx.cond(
        forecast["status"] == "evaluated",
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
        rx.el.span("—", class_name="text-xs text-gray-400 tabular-nums"),
    )


def _confidence_cell(forecast: ForecastWindow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                class_name="h-full bg-blue-600 rounded-full",
                style={"width": f"{forecast['confidence'] * 100}%"},
            ),
            class_name="h-1 w-12 bg-gray-100 rounded-full overflow-hidden",
        ),
        rx.el.span(
            f"{(forecast['confidence'] * 100):.0f}%",
            class_name="text-[11px] font-semibold text-gray-700 tabular-nums",
        ),
        class_name="flex items-center gap-1.5",
    )


def _table_row(forecast: ForecastWindow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    forecast["target_symbol"],
                    class_name="text-[10px] font-bold text-white",
                ),
                class_name="h-6 w-6 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.el.span(
                forecast["target_symbol"],
                class_name="text-xs font-semibold text-gray-900",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.el.span(
                forecast["model_slot"],
                class_name="text-[10px] font-bold text-purple-700 px-1.5 py-0.5 rounded bg-purple-50 border border-purple-100",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.el.span(
                forecast["horizon"],
                class_name="text-[11px] font-semibold text-blue-700 px-1.5 py-0.5 rounded-md bg-blue-50 border border-blue-100",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(_direction_cell(forecast), class_name="px-3 py-2.5"),
        rx.el.td(_actual_cell(forecast), class_name="px-3 py-2.5"),
        rx.el.td(
            rx.cond(
                forecast["status"] == "evaluated",
                rx.el.span(
                    f"{forecast['abs_error']:.2f}%",
                    class_name="text-xs font-medium text-gray-700 tabular-nums",
                ),
                rx.el.span("—", class_name="text-xs text-gray-400"),
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(_confidence_cell(forecast), class_name="px-3 py-2.5"),
        rx.el.td(_status_badge(forecast), class_name="px-3 py-2.5"),
        rx.el.td(
            rx.el.span(
                forecast["generated_at"],
                class_name="text-[11px] text-gray-500 tabular-nums",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.el.span(
                forecast["matures_at"],
                class_name="text-[11px] text-gray-500 tabular-nums",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.cond(
                forecast["model"] != "",
                rx.el.span(
                    forecast["model"],
                    class_name="text-[11px] font-mono text-gray-600",
                ),
                rx.el.span("—", class_name="text-[11px] text-gray-400"),
            ),
            class_name="px-3 py-2.5",
        ),
        class_name="border-b border-gray-100 hover:bg-gray-50 transition-colors",
    )


def _table_header() -> rx.Component:
    headers = [
        ("", "asset-icon"),
        ("Asset", "coins"),
        ("Slot", "trophy"),
        ("Horizon", "clock"),
        ("Predicted", "trending-up"),
        ("Actual", "activity"),
        ("Abs Error", "ruler"),
        ("Confidence", "gauge"),
        ("Status", "shield-check"),
        ("Generated", "calendar"),
        ("Matures", "calendar-clock"),
        ("Model", "brain"),
    ]
    return rx.el.thead(
        rx.el.tr(
            rx.foreach(
                headers,
                lambda h: rx.el.th(
                    rx.el.span(
                        h[0],
                        class_name="text-[10px] font-semibold text-gray-500 uppercase tracking-wider",
                    ),
                    class_name="px-3 py-2.5 text-left bg-gray-50 border-b border-gray-200",
                ),
            ),
        ),
    )


def _empty_table_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("inbox", class_name="h-5 w-5 text-gray-400"),
            class_name="h-10 w-10 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center mb-3",
        ),
        rx.el.p(
            rx.cond(
                DashboardState.total_forecasts == 0,
                "No predictions generated yet",
                "No predictions match these filters",
            ),
            class_name="text-sm font-semibold text-gray-900 mb-1",
        ),
        rx.el.p(
            rx.cond(
                DashboardState.total_forecasts == 0,
                "Run predictions from the Forecast Windows panel above to populate this table.",
                "Try resetting filters to see all predictions in scope.",
            ),
            class_name="text-xs text-gray-500 max-w-md text-center",
        ),
        rx.cond(
            DashboardState.total_forecasts > 0,
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-3.5 w-3.5"),
                rx.el.span("Reset filters", class_name="text-xs font-semibold"),
                on_click=PerformanceState.reset_filters,
                class_name="mt-3 flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gray-900 hover:bg-gray-800 text-white transition-colors",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col items-center justify-center py-12",
    )


def _action_buttons() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.cond(
                DashboardState.market_loading,
                rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
                rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
            ),
            rx.el.span(
                rx.cond(
                    DashboardState.market_loading,
                    "Refreshing…",
                    "Refresh Markets",
                ),
                class_name="text-xs font-semibold",
            ),
            on_click=DashboardState.refresh_market_data,
            disabled=DashboardState.market_loading,
            class_name="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 transition-colors disabled:opacity-60 disabled:cursor-not-allowed",
        ),
        rx.el.button(
            rx.cond(
                DashboardState.predictions_loading,
                rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
                rx.icon("trophy", class_name="h-3.5 w-3.5"),
            ),
            rx.el.span(
                rx.cond(
                    DashboardState.predictions_loading,
                    "Running…",
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
        ),
        class_name="flex items-center gap-2 flex-wrap",
    )


def _readiness_banner() -> rx.Component:
    return rx.cond(
        ~DashboardState.llm_router_ready | ~DashboardState.has_market_data,
        rx.el.div(
            rx.icon(
                "circle-alert",
                class_name="h-4 w-4 text-amber-600 shrink-0 mt-0.5",
            ),
            rx.el.div(
                rx.el.p(
                    rx.cond(
                        ~DashboardState.llm_router_ready,
                        "OpenRouter is not configured",
                        "Market data unavailable",
                    ),
                    class_name="text-xs font-semibold text-amber-900",
                ),
                rx.el.p(
                    rx.cond(
                        ~DashboardState.llm_router_ready,
                        "Set OPENROUTER_API_KEY to enable prediction generation. Refresh remains available.",
                        "Refresh markets first to enable prediction generation.",
                    ),
                    class_name="text-[11px] text-amber-700",
                ),
            ),
            class_name="flex items-start gap-2 p-3 rounded-lg bg-amber-50 border border-amber-100 mb-3",
        ),
        rx.fragment(),
    )


def performance_section() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("line-chart", class_name="h-4 w-4 text-gray-600"),
                    rx.el.h2(
                        "Model Performance",
                        class_name="text-base font-semibold text-gray-900",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    "Live history of every prediction with directional accuracy, error, and provider metadata",
                    class_name="text-xs text-gray-500",
                ),
            ),
            _action_buttons(),
            class_name="flex items-start justify-between gap-3 mb-4 flex-wrap",
        ),
        _readiness_banner(),
        _summary_metrics(),
        _filters_panel(),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "Prediction Log",
                        class_name="text-sm font-semibold text-gray-900",
                    ),
                    rx.el.p(
                        f"Showing {DashboardState.filtered_count} of {DashboardState.total_forecasts} predictions",
                        class_name="text-[11px] text-gray-500",
                    ),
                ),
                rx.cond(
                    DashboardState.market_error != "",
                    rx.el.div(
                        rx.icon(
                            "circle-alert",
                            class_name="h-3.5 w-3.5 text-red-600",
                        ),
                        rx.el.span(
                            DashboardState.market_error,
                            class_name="text-[11px] font-medium text-red-700",
                        ),
                        class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-red-50 border border-red-100",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center justify-between p-4 border-b border-gray-100 gap-3 flex-wrap",
            ),
            rx.cond(
                DashboardState.filtered_count > 0,
                rx.el.div(
                    rx.el.table(
                        _table_header(),
                        rx.el.tbody(
                            rx.foreach(
                                DashboardState.filtered_forecasts, _table_row
                            ),
                        ),
                        class_name="table-auto w-full min-w-[1200px]",
                    ),
                    class_name="overflow-x-auto",
                ),
                _empty_table_state(),
            ),
            class_name="rounded-xl bg-white border border-gray-200 overflow-hidden",
        ),
        class_name="mb-6",
    )