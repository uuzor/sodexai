import reflex as rx
from app.states.dashboard_state import DashboardState, ForecastWindow


def _direction_chip(forecast: ForecastWindow) -> rx.Component:
    is_up = forecast["direction"] == "up"
    return rx.el.div(
        rx.cond(
            is_up,
            rx.icon("arrow-up-right", class_name="h-3 w-3 text-emerald-700"),
            rx.icon("arrow-down-right", class_name="h-3 w-3 text-red-700"),
        ),
        rx.el.span(
            rx.cond(
                is_up,
                f"+{forecast['predicted_change']:.2f}%",
                f"{forecast['predicted_change']:.2f}%",
            ),
            class_name=rx.cond(
                is_up,
                "text-[11px] font-semibold text-emerald-700 tabular-nums",
                "text-[11px] font-semibold text-red-700 tabular-nums",
            ),
        ),
        class_name=rx.cond(
            is_up,
            "flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-emerald-50 border border-emerald-100 w-fit",
            "flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-red-50 border border-red-100 w-fit",
        ),
    )


def _status_dot(forecast: ForecastWindow) -> rx.Component:
    return rx.match(
        forecast["status"],
        (
            "evaluated",
            rx.cond(
                forecast["correct"],
                rx.el.div(
                    rx.icon("check", class_name="h-2.5 w-2.5 text-emerald-700"),
                    class_name="h-4 w-4 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center",
                ),
                rx.el.div(
                    rx.icon("x", class_name="h-2.5 w-2.5 text-red-700"),
                    class_name="h-4 w-4 rounded-full bg-red-50 border border-red-200 flex items-center justify-center",
                ),
            ),
        ),
        (
            "failed",
            rx.el.div(
                rx.icon("circle-alert", class_name="h-2.5 w-2.5 text-red-700"),
                class_name="h-4 w-4 rounded-full bg-red-50 border border-red-200 flex items-center justify-center",
            ),
        ),
        rx.el.div(
            class_name="h-2 w-2 rounded-full bg-amber-500 animate-pulse",
        ),
    )


def _forecast_cell(forecast: ForecastWindow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                forecast["horizon"],
                class_name="text-[10px] font-bold text-blue-700 px-1 py-0.5 rounded bg-blue-50 border border-blue-100",
            ),
            _status_dot(forecast),
            class_name="flex items-center justify-between mb-1.5",
        ),
        rx.cond(
            forecast["status"] == "failed",
            rx.el.div(
                rx.el.span(
                    "Failed",
                    class_name="text-[10px] font-semibold text-red-700",
                ),
                class_name="px-1.5 py-0.5 rounded-md bg-red-50 border border-red-100 w-fit",
            ),
            _direction_chip(forecast),
        ),
        rx.cond(
            forecast["status"] != "failed",
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        class_name="h-full bg-blue-600 rounded-full",
                        style={"width": f"{forecast['confidence'] * 100}%"},
                    ),
                    class_name="h-1 w-full bg-gray-100 rounded-full overflow-hidden",
                ),
                rx.el.span(
                    f"{(forecast['confidence'] * 100):.0f}%",
                    class_name="text-[10px] font-semibold text-gray-600 tabular-nums",
                ),
                class_name="flex items-center gap-1.5 mt-1.5",
            ),
            rx.fragment(),
        ),
        rx.cond(
            forecast["status"] == "evaluated",
            rx.el.div(
                rx.el.span(
                    "Actual",
                    class_name="text-[9px] text-gray-400 uppercase tracking-wider",
                ),
                rx.el.span(
                    rx.cond(
                        forecast["actual_change"] >= 0,
                        f"+{forecast['actual_change']:.2f}%",
                        f"{forecast['actual_change']:.2f}%",
                    ),
                    class_name=rx.cond(
                        forecast["actual_change"] >= 0,
                        "text-[10px] font-semibold text-emerald-600 tabular-nums",
                        "text-[10px] font-semibold text-red-600 tabular-nums",
                    ),
                ),
                class_name="flex items-center justify-between mt-1.5 pt-1.5 border-t border-gray-100",
            ),
            rx.fragment(),
        ),
        class_name="p-2 rounded-lg bg-gray-50 border border-gray-200",
    )


def _model_column(slot_label: str, asset_symbol: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                slot_label,
                class_name="text-[10px] font-bold text-purple-700 px-1.5 py-0.5 rounded bg-purple-50 border border-purple-100",
            ),
            class_name="mb-1.5",
        ),
        rx.foreach(
            DashboardState.forecasts,
            lambda f: rx.cond(
                (f["model_slot"] == slot_label)
                & (f["target_symbol"] == asset_symbol),
                _forecast_cell(f),
                rx.fragment(),
            ),
        ),
        class_name="flex flex-col gap-1.5 min-w-0",
    )


def _asset_row(asset) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    asset["symbol"],
                    class_name="text-xs font-bold text-white",
                ),
                class_name="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    asset["symbol"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"${asset['price']:,.2f}",
                    class_name="text-[11px] text-gray-500 tabular-nums",
                ),
            ),
            class_name="flex items-center gap-2 mb-3",
        ),
        rx.el.div(
            rx.foreach(
                DashboardState.competition_model_slots,
                lambda slot: _model_column(slot["slot"], asset["symbol"]),
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-2",
        ),
        class_name="p-3 rounded-xl bg-white border border-gray-200",
    )


def _empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("layout-grid", class_name="h-5 w-5 text-gray-400"),
            class_name="h-10 w-10 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center mb-3",
        ),
        rx.el.p(
            "No competition results yet",
            class_name="text-sm font-semibold text-gray-900 mb-1",
        ),
        rx.el.p(
            "Run the competition to see all 3 models compared across every asset and horizon.",
            class_name="text-xs text-gray-500 max-w-md text-center",
        ),
        class_name="flex flex-col items-center justify-center py-12 rounded-xl bg-white border border-dashed border-gray-300",
    )


def competition_grid() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("layout-grid", class_name="h-4 w-4 text-blue-600"),
                    rx.el.h2(
                        "Per-Asset Model Comparison",
                        class_name="text-base font-semibold text-gray-900",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    "Side-by-side forecasts from every model across every horizon for each asset",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.el.div(
                rx.el.span(
                    f"{DashboardState.total_forecasts} predictions tracked",
                    class_name="text-[11px] font-medium text-gray-600 px-2 py-1 rounded-md bg-gray-50 border border-gray-200",
                ),
                rx.cond(
                    DashboardState.pending_count > 0,
                    rx.el.span(
                        f"{DashboardState.pending_count} pending",
                        class_name="text-[11px] font-semibold text-amber-700 px-2 py-1 rounded-md bg-amber-50 border border-amber-100",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    DashboardState.evaluated_count > 0,
                    rx.el.span(
                        f"{DashboardState.evaluated_count} evaluated",
                        class_name="text-[11px] font-semibold text-emerald-700 px-2 py-1 rounded-md bg-emerald-50 border border-emerald-100",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center gap-2 flex-wrap",
            ),
            class_name="flex items-start justify-between gap-3 mb-4 flex-wrap",
        ),
        rx.cond(
            DashboardState.total_forecasts > 0,
            rx.el.div(
                rx.foreach(DashboardState.market_assets, _asset_row),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-3",
            ),
            _empty_state(),
        ),
        class_name="mb-6",
    )