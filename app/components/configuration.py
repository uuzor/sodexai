import reflex as rx
from app.states.dashboard_state import DashboardState


def provider_credential_row(
    label: str, description: str, configured: rx.Var, source: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    label, class_name="text-xs font-semibold text-gray-900"
                ),
                rx.el.p(
                    description, class_name="text-[11px] text-gray-500 mt-0.5"
                ),
                rx.el.p(
                    source,
                    class_name="text-[10px] text-gray-400 font-mono mt-1",
                ),
            ),
            rx.cond(
                configured,
                rx.el.div(
                    rx.icon(
                        "circle-check",
                        class_name="h-3.5 w-3.5 text-emerald-600",
                    ),
                    rx.el.span(
                        "Configured",
                        class_name="text-[11px] font-semibold text-emerald-700",
                    ),
                    class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-emerald-50 border border-emerald-100 shrink-0",
                ),
                rx.el.div(
                    rx.icon(
                        "circle-alert",
                        class_name="h-3.5 w-3.5 text-amber-600",
                    ),
                    rx.el.span(
                        "Missing",
                        class_name="text-[11px] font-semibold text-amber-700",
                    ),
                    class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-50 border border-amber-100 shrink-0",
                ),
            ),
            class_name="flex items-start justify-between gap-3",
        ),
        class_name="p-3 border border-gray-100 rounded-lg bg-gray-50",
    )


def cadence_button(option: str) -> rx.Component:
    is_active = DashboardState.forecast_cadence == option
    return rx.el.button(
        option,
        on_click=lambda: DashboardState.set_cadence(option),
        class_name=rx.cond(
            is_active,
            "px-3 py-1.5 rounded-md text-xs font-semibold bg-blue-600 text-white border border-blue-600 transition-colors",
            "px-3 py-1.5 rounded-md text-xs font-medium bg-white text-gray-700 border border-gray-200 hover:border-gray-300 transition-colors",
        ),
    )


def configuration_section() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("settings", class_name="h-4 w-4 text-gray-600"),
                    rx.el.h2(
                        "Configuration",
                        class_name="text-base font-semibold text-gray-900",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    "API credentials, prediction target, and forecast cadence",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.cond(
                DashboardState.credentials_ready,
                rx.el.div(
                    rx.icon(
                        "shield-check",
                        class_name="h-3.5 w-3.5 text-emerald-600",
                    ),
                    rx.el.span(
                        "Ready",
                        class_name="text-xs font-semibold text-emerald-700",
                    ),
                    class_name="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-100",
                ),
                rx.el.div(
                    rx.icon(
                        "shield-alert", class_name="h-3.5 w-3.5 text-amber-600"
                    ),
                    rx.el.span(
                        "Needs Setup",
                        class_name="text-xs font-semibold text-amber-700",
                    ),
                    class_name="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50 border border-amber-100",
                ),
            ),
            class_name="flex items-center justify-between mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "Provider Credentials",
                        class_name="text-sm font-semibold text-gray-900 mb-1",
                    ),
                    rx.el.p(
                        "Provider keys are read from secure environment variables — never stored in client state.",
                        class_name="text-xs text-gray-500 mb-4",
                    ),
                    rx.el.div(
                        provider_credential_row(
                            "SoSoValue",
                            "Primary market data — currencies + market-snapshot endpoints",
                            DashboardState.credentials_ready,
                            "env: SOSOVALUE_API_KEY / SOSO_API_KEY",
                        ),
                        provider_credential_row(
                            "SoDEX (testnet)",
                            "Public testnet ticker endpoint — no key required",
                            DashboardState.sodex_public,
                            "https://testnet-gw.sodex.dev/api/v1/spot/markets/tickers",
                        ),
                        provider_credential_row(
                            "OpenRouter",
                            "Structured forecast generation — live prediction engine",
                            DashboardState.llm_router_ready,
                            "env: OPENROUTER_API_KEY (+ optional OPENROUTER_MODEL)",
                        ),
                        class_name="flex flex-col gap-2 mb-4",
                    ),
                    rx.el.button(
                        rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
                        rx.el.span(
                            "Trigger Manual Refresh",
                            class_name="text-xs font-semibold",
                        ),
                        on_click=DashboardState.refresh_market_data,
                        disabled=DashboardState.market_loading,
                        class_name="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-60 disabled:cursor-not-allowed",
                    ),
                    class_name="p-5",
                ),
                class_name="rounded-xl bg-white border border-gray-200",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "Active Prediction Target",
                        class_name="text-sm font-semibold text-gray-900 mb-1",
                    ),
                    rx.el.p(
                        "Asset currently in scope for forecast generation.",
                        class_name="text-xs text-gray-500 mb-3",
                    ),
                    rx.el.div(
                        rx.foreach(
                            DashboardState.market_assets,
                            lambda a: rx.el.button(
                                a["symbol"],
                                on_click=lambda: (
                                    DashboardState.set_active_target(
                                        a["symbol"]
                                    )
                                ),
                                class_name=rx.cond(
                                    DashboardState.active_target == a["symbol"],
                                    "px-3 py-1.5 rounded-md text-xs font-semibold bg-blue-600 text-white border border-blue-600 transition-colors",
                                    "px-3 py-1.5 rounded-md text-xs font-medium bg-white text-gray-700 border border-gray-200 hover:border-gray-300 transition-colors",
                                ),
                            ),
                        ),
                        class_name="flex flex-wrap gap-2",
                    ),
                    class_name="p-5 border-b border-gray-100",
                ),
                rx.el.div(
                    rx.el.h3(
                        "Forecast Cadence",
                        class_name="text-sm font-semibold text-gray-900 mb-1",
                    ),
                    rx.el.p(
                        "How often the engine generates a fresh prediction batch.",
                        class_name="text-xs text-gray-500 mb-3",
                    ),
                    rx.el.div(
                        rx.foreach(
                            DashboardState.cadence_options, cadence_button
                        ),
                        class_name="flex flex-wrap gap-2",
                    ),
                    rx.el.div(
                        rx.icon(
                            "info",
                            class_name="h-3.5 w-3.5 text-blue-600 shrink-0 mt-0.5",
                        ),
                        rx.el.p(
                            "Scheduled runs activate automatically once Phase 2 ingestion is enabled.",
                            class_name="text-[11px] text-gray-600",
                        ),
                        class_name="flex items-start gap-2 mt-4 p-2.5 rounded-lg bg-blue-50 border border-blue-100",
                    ),
                    class_name="p-5",
                ),
                class_name="rounded-xl bg-white border border-gray-200",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-4",
        ),
        class_name="mb-6",
    )