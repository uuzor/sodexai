import reflex as rx
from app.states.dashboard_state import DashboardState, ModelLeaderboardEntry


def _status_badge(status: rx.Var) -> rx.Component:
    return rx.match(
        status,
        (
            "healthy",
            rx.el.div(
                rx.el.div(class_name="h-1.5 w-1.5 rounded-full bg-emerald-500"),
                rx.el.span(
                    "Healthy",
                    class_name="text-[10px] font-semibold text-emerald-700",
                ),
                class_name="flex items-center gap-1.5 px-1.5 py-0.5 rounded-md bg-emerald-50 border border-emerald-100 w-fit",
            ),
        ),
        (
            "degraded",
            rx.el.div(
                rx.el.div(class_name="h-1.5 w-1.5 rounded-full bg-amber-500"),
                rx.el.span(
                    "Degraded",
                    class_name="text-[10px] font-semibold text-amber-700",
                ),
                class_name="flex items-center gap-1.5 px-1.5 py-0.5 rounded-md bg-amber-50 border border-amber-100 w-fit",
            ),
        ),
        (
            "error",
            rx.el.div(
                rx.el.div(class_name="h-1.5 w-1.5 rounded-full bg-red-500"),
                rx.el.span(
                    "Error",
                    class_name="text-[10px] font-semibold text-red-700",
                ),
                class_name="flex items-center gap-1.5 px-1.5 py-0.5 rounded-md bg-red-50 border border-red-100 w-fit",
            ),
        ),
        rx.el.div(
            rx.el.span(
                "Idle", class_name="text-[10px] font-semibold text-gray-600"
            ),
            class_name="px-1.5 py-0.5 rounded-md bg-gray-50 border border-gray-200 w-fit",
        ),
    )


def _accuracy_bar(accuracy: rx.Var, evaluated: rx.Var) -> rx.Component:
    return rx.cond(
        evaluated > 0,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    class_name="h-full bg-emerald-500 rounded-full",
                    style={"width": f"{accuracy}%"},
                ),
                class_name="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden",
            ),
            rx.el.span(
                f"{accuracy:.1f}%",
                class_name="text-xs font-semibold text-gray-900 tabular-nums",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.span("—", class_name="text-xs text-gray-400 tabular-nums"),
    )


def _leaderboard_row(entry: ModelLeaderboardEntry, index: int) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    f"#{index + 1}",
                    class_name="text-[11px] font-bold text-gray-700 tabular-nums",
                ),
                class_name="h-6 w-7 rounded-md bg-gray-50 border border-gray-200 flex items-center justify-center",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    entry["model_slot"],
                    class_name="text-[10px] font-bold text-purple-700 px-1.5 py-0.5 rounded bg-purple-50 border border-purple-100 w-fit",
                ),
                rx.el.span(
                    entry["model"],
                    class_name="text-[11px] font-mono text-gray-600 truncate max-w-[260px]",
                ),
                class_name="flex flex-col gap-1",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(_status_badge(entry["status"]), class_name="px-3 py-2.5"),
        rx.el.td(
            _accuracy_bar(entry["directional_accuracy"], entry["evaluated"]),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.cond(
                entry["evaluated"] > 0,
                rx.el.span(
                    f"{entry['avg_abs_error']:.2f}%",
                    class_name="text-xs font-semibold text-gray-900 tabular-nums",
                ),
                rx.el.span(
                    "—", class_name="text-xs text-gray-400 tabular-nums"
                ),
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.el.span(
                entry["evaluated"].to_string(),
                class_name="text-xs font-semibold text-emerald-700 tabular-nums",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.el.span(
                entry["pending"].to_string(),
                class_name="text-xs font-semibold text-amber-700 tabular-nums",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.el.span(
                entry["failed"].to_string(),
                class_name=rx.cond(
                    entry["failed"] > 0,
                    "text-xs font-semibold text-red-700 tabular-nums",
                    "text-xs font-medium text-gray-400 tabular-nums",
                ),
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.cond(
                entry["best_asset"] != "",
                rx.el.div(
                    rx.el.span(
                        entry["best_asset"],
                        class_name="text-[10px] font-bold text-white",
                    ),
                    rx.el.span(
                        f"{entry['best_asset_accuracy']:.0f}%",
                        class_name="text-[11px] font-semibold text-gray-700 tabular-nums",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.span(
                    "—", class_name="text-xs text-gray-400 tabular-nums"
                ),
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.cond(
                entry["avg_confidence"] > 0,
                rx.el.span(
                    f"{(entry['avg_confidence'] * 100):.0f}%",
                    class_name="text-xs font-medium text-gray-700 tabular-nums",
                ),
                rx.el.span(
                    "—", class_name="text-xs text-gray-400 tabular-nums"
                ),
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            rx.cond(
                entry["latest_run"] != "",
                rx.el.span(
                    entry["latest_run"],
                    class_name="text-[11px] text-gray-500 tabular-nums",
                ),
                rx.el.span("Never", class_name="text-[11px] text-gray-400"),
            ),
            class_name="px-3 py-2.5",
        ),
        class_name="border-b border-gray-100 hover:bg-gray-50 transition-colors",
    )


def _row_with_index(entry: ModelLeaderboardEntry, index: int) -> rx.Component:
    return _leaderboard_row(entry, index)


def _leaderboard_header() -> rx.Component:
    headers = [
        "Rank",
        "Model",
        "Status",
        "Directional Accuracy",
        "Mean Abs Error",
        "Evaluated",
        "Pending",
        "Failed",
        "Best Asset",
        "Avg Confidence",
        "Latest Run",
    ]
    return rx.el.thead(
        rx.el.tr(
            rx.foreach(
                headers,
                lambda h: rx.el.th(
                    rx.el.span(
                        h,
                        class_name="text-[10px] font-semibold text-gray-500 uppercase tracking-wider",
                    ),
                    class_name="px-3 py-2.5 text-left bg-gray-50 border-b border-gray-200",
                ),
            ),
        ),
    )


def _empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("trophy", class_name="h-5 w-5 text-gray-400"),
            class_name="h-10 w-10 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center mb-3",
        ),
        rx.el.p(
            "No model results yet",
            class_name="text-sm font-semibold text-gray-900 mb-1",
        ),
        rx.el.p(
            "Run the prediction competition to populate the model leaderboard.",
            class_name="text-xs text-gray-500 max-w-md text-center",
        ),
        class_name="flex flex-col items-center justify-center py-12",
    )


def leaderboard() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("trophy", class_name="h-4 w-4 text-purple-600"),
                    rx.el.h2(
                        "Model Leaderboard",
                        class_name="text-base font-semibold text-gray-900",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    "Per-model directional accuracy, error, and reliability across all assets and horizons",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.el.div(
                rx.el.span(
                    f"{DashboardState.model_leaderboard.length()} models tracked",
                    class_name="text-[11px] font-medium text-gray-600 px-2 py-1 rounded-md bg-gray-50 border border-gray-200",
                ),
                rx.cond(
                    DashboardState.failed_count > 0,
                    rx.el.span(
                        f"{DashboardState.failed_count} failed calls",
                        class_name="text-[11px] font-semibold text-red-700 px-2 py-1 rounded-md bg-red-50 border border-red-100",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center gap-2 flex-wrap",
            ),
            class_name="flex items-start justify-between gap-3 mb-4 flex-wrap",
        ),
        rx.el.div(
            rx.cond(
                DashboardState.model_leaderboard.length() > 0,
                rx.el.div(
                    rx.el.table(
                        _leaderboard_header(),
                        rx.el.tbody(
                            rx.foreach(
                                DashboardState.model_leaderboard,
                                _row_with_index,
                            ),
                        ),
                        class_name="table-auto w-full min-w-[1100px]",
                    ),
                    class_name="overflow-x-auto",
                ),
                _empty_state(),
            ),
            class_name="rounded-xl bg-white border border-gray-200 overflow-hidden",
        ),
        class_name="mb-6",
    )