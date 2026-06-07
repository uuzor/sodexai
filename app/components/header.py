import reflex as rx
from app.states.dashboard_state import DashboardState


def header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    DashboardState.active_nav,
                    class_name="text-xl font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Real-time crypto market intelligence and forecast operations",
                    class_name="text-sm text-gray-500",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "search",
                        class_name="h-4 w-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2",
                    ),
                    rx.el.input(
                        placeholder="Search markets, models, predictions...",
                        class_name="pl-9 pr-3 py-2 w-72 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    ),
                    class_name="relative hidden lg:block",
                ),
                rx.el.button(
                    rx.icon("bell", class_name="h-4 w-4 text-gray-600"),
                    class_name="h-9 w-9 rounded-lg border border-gray-200 hover:bg-gray-50 flex items-center justify-center transition-colors",
                ),
                rx.el.button(
                    rx.cond(
                        DashboardState.market_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin",
                        ),
                        rx.icon("refresh-cw", class_name="h-4 w-4"),
                    ),
                    rx.el.span(
                        rx.cond(
                            DashboardState.market_loading,
                            "Refreshing…",
                            "Refresh",
                        ),
                        class_name="text-sm font-medium",
                    ),
                    on_click=DashboardState.refresh_market_data,
                    disabled=DashboardState.market_loading,
                    class_name="flex items-center gap-2 px-3 h-9 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-60 disabled:cursor-not-allowed",
                ),
                class_name="flex items-center gap-3",
            ),
            class_name="flex items-center justify-between px-6 h-16",
        ),
        class_name="bg-white border-b border-gray-200 sticky top-0 z-10",
    )