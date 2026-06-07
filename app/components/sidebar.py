import reflex as rx
from app.states.dashboard_state import DashboardState


def nav_link(item: dict[str, str]) -> rx.Component:
    is_active = DashboardState.active_nav == item["label"]
    return rx.el.button(
        rx.icon(item["icon"], class_name="h-4 w-4"),
        rx.el.span(item["label"], class_name="text-sm font-medium"),
        on_click=lambda: DashboardState.set_active_nav(item["label"]),
        class_name=rx.cond(
            is_active,
            "flex items-center gap-3 px-3 py-2 rounded-lg bg-blue-50 text-blue-700 border border-blue-100 w-full transition-colors",
            "flex items-center gap-3 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-gray-900 border border-transparent w-full transition-colors",
        ),
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("activity", class_name="h-5 w-5 text-white"),
                    class_name="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center",
                ),
                rx.el.div(
                    rx.el.p(
                        "CryptoForecast",
                        class_name="text-sm font-semibold text-gray-900 leading-tight",
                    ),
                    rx.el.p(
                        "Prediction Engine", class_name="text-xs text-gray-500"
                    ),
                ),
                class_name="flex items-center gap-3 px-4 h-16 border-b border-gray-200",
            ),
            rx.el.nav(
                rx.el.p(
                    "MAIN",
                    class_name="text-[10px] font-semibold text-gray-400 tracking-wider px-2 mb-2",
                ),
                rx.foreach(DashboardState.nav_items, nav_link),
                class_name="flex flex-col gap-1 p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            class_name="h-2 w-2 rounded-full bg-amber-400"
                        ),
                        rx.el.p(
                            "System Status",
                            class_name="text-xs font-semibold text-gray-700",
                        ),
                        class_name="flex items-center gap-2 mb-1",
                    ),
                    rx.el.p(
                        f"{DashboardState.connected_count}/{DashboardState.total_providers} providers connected",
                        class_name="text-xs text-gray-500",
                    ),
                    rx.cond(
                        DashboardState.last_refresh != "",
                        rx.el.p(
                            f"Last sync {DashboardState.last_refresh}",
                            class_name="text-[11px] text-emerald-600 font-medium mt-1",
                        ),
                        rx.el.p(
                            "Awaiting first refresh",
                            class_name="text-[11px] text-amber-600 font-medium mt-1",
                        ),
                    ),
                    class_name="p-3 rounded-lg bg-gray-50 border border-gray-200",
                ),
                class_name="mt-auto p-3 border-t border-gray-200",
            ),
            class_name="flex flex-col h-screen",
        ),
        class_name="w-64 shrink-0 bg-white border-r border-gray-200 hidden md:flex flex-col sticky top-0",
    )