import reflex as rx
from app.states.dashboard_state import DashboardState, MarketAsset


def asset_card(asset: MarketAsset) -> rx.Component:
    is_active = DashboardState.active_target == asset["symbol"]
    is_up = asset["change_24h"] >= 0
    return rx.el.button(
        rx.el.div(
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
                        asset["name"],
                        class_name="text-sm font-semibold text-gray-900 text-left",
                    ),
                    rx.el.p(
                        asset["symbol"],
                        class_name="text-xs text-gray-500 text-left",
                    ),
                ),
                class_name="flex items-center gap-2",
            ),
            rx.cond(
                is_active,
                rx.el.div(
                    rx.icon("check", class_name="h-3 w-3 text-white"),
                    class_name="h-5 w-5 rounded-full bg-blue-600 flex items-center justify-center",
                ),
                rx.el.div(class_name="h-5 w-5"),
            ),
            class_name="flex items-center justify-between mb-3",
        ),
        rx.el.p(
            f"${asset['price']:,.2f}",
            class_name="text-xl font-bold text-gray-900 text-left tabular-nums",
        ),
        rx.el.div(
            rx.cond(
                is_up,
                rx.el.div(
                    rx.icon("trending-up", class_name="h-3 w-3"),
                    rx.el.span(
                        f"+{asset['change_24h']:.2f}%",
                        class_name="text-xs font-semibold tabular-nums",
                    ),
                    class_name="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md w-fit",
                ),
                rx.el.div(
                    rx.icon("trending-down", class_name="h-3 w-3"),
                    rx.el.span(
                        f"{asset['change_24h']:.2f}%",
                        class_name="text-xs font-semibold tabular-nums",
                    ),
                    class_name="flex items-center gap-1 text-red-600 bg-red-50 px-2 py-0.5 rounded-md w-fit",
                ),
            ),
            rx.el.p(
                f"Vol ${(asset['volume_24h'] / 1000000000):.2f}B",
                class_name="text-[11px] text-gray-500 tabular-nums",
            ),
            class_name="flex items-center justify-between mt-2",
        ),
        rx.el.div(
            rx.icon("radio", class_name="h-3 w-3 text-gray-400"),
            rx.el.span(
                f"via {asset['source']}",
                class_name="text-[10px] text-gray-400 font-medium",
            ),
            class_name="flex items-center gap-1 mt-2 pt-2 border-t border-gray-100",
        ),
        on_click=lambda: DashboardState.set_active_target(asset["symbol"]),
        class_name=rx.cond(
            is_active,
            "p-4 rounded-xl bg-white border-2 border-blue-500 transition-all text-left hover:border-blue-600",
            "p-4 rounded-xl bg-white border border-gray-200 hover:border-gray-300 transition-all text-left",
        ),
    )


def _skeleton_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-8 w-8 rounded-full bg-gray-200 animate-pulse mb-3"
        ),
        rx.el.div(class_name="h-6 w-32 bg-gray-200 rounded animate-pulse mb-2"),
        rx.el.div(class_name="h-4 w-20 bg-gray-200 rounded animate-pulse"),
        class_name="p-4 rounded-xl bg-white border border-gray-200",
    )


def _skeleton_grid() -> rx.Component:
    return rx.el.div(
        _skeleton_card(),
        _skeleton_card(),
        _skeleton_card(),
        _skeleton_card(),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3",
    )


def _empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("cloud-off", class_name="h-5 w-5 text-amber-600"),
            class_name="h-10 w-10 rounded-full bg-amber-50 flex items-center justify-center mb-3",
        ),
        rx.el.p(
            "No market data available",
            class_name="text-sm font-semibold text-gray-900 mb-1",
        ),
        rx.el.p(
            rx.cond(
                DashboardState.market_error != "",
                DashboardState.market_error,
                "Click Refresh to fetch live quotes from SoSoValue and SoDEX.",
            ),
            class_name="text-xs text-gray-500 max-w-md text-center",
        ),
        rx.el.button(
            rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
            rx.el.span("Refresh now", class_name="text-xs font-semibold"),
            on_click=DashboardState.refresh_market_data,
            class_name="mt-3 flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white transition-colors",
        ),
        class_name="flex flex-col items-center justify-center py-12 rounded-xl bg-white border border-dashed border-gray-300",
    )


def market_summary() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Market Summary",
                    class_name="text-base font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Live data from SoSoValue and SoDEX testnet — select an asset to set the active prediction target",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.el.div(
                rx.cond(
                    DashboardState.market_loading,
                    rx.el.div(
                        rx.el.div(
                            class_name="h-2 w-2 rounded-full bg-blue-500 animate-pulse"
                        ),
                        rx.el.span(
                            "Refreshing…",
                            class_name="text-xs text-gray-600 font-medium",
                        ),
                        class_name="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-50 border border-blue-100",
                    ),
                    rx.cond(
                        DashboardState.has_market_data,
                        rx.el.div(
                            rx.el.div(
                                class_name="h-2 w-2 rounded-full bg-emerald-500"
                            ),
                            rx.el.span(
                                f"Updated {DashboardState.last_refresh}",
                                class_name="text-xs text-gray-600 font-medium",
                            ),
                            class_name="flex items-center gap-2 px-3 py-1.5 rounded-md bg-gray-50 border border-gray-200",
                        ),
                        rx.el.div(
                            rx.el.div(
                                class_name="h-2 w-2 rounded-full bg-amber-500"
                            ),
                            rx.el.span(
                                "No data yet",
                                class_name="text-xs text-gray-600 font-medium",
                            ),
                            class_name="flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-50 border border-amber-100",
                        ),
                    ),
                ),
            ),
            class_name="flex items-center justify-between mb-4",
        ),
        rx.cond(
            DashboardState.market_loading & ~DashboardState.has_market_data,
            _skeleton_grid(),
            rx.cond(
                DashboardState.has_market_data,
                rx.el.div(
                    rx.foreach(DashboardState.market_assets, asset_card),
                    class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3",
                ),
                _empty_state(),
            ),
        ),
        class_name="mb-6",
    )