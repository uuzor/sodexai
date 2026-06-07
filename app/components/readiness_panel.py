import reflex as rx
from app.states.dashboard_state import DashboardState


def _step(
    icon: str,
    title: str,
    description,
    ok: rx.Var,
    pending_label: str,
    ok_label: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.cond(
                ok,
                rx.el.div(
                    rx.icon("check", class_name="h-3.5 w-3.5 text-white"),
                    class_name="h-7 w-7 rounded-full bg-emerald-500 flex items-center justify-center shrink-0",
                ),
                rx.el.div(
                    rx.icon(icon, class_name="h-3.5 w-3.5 text-amber-600"),
                    class_name="h-7 w-7 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center shrink-0",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        title,
                        class_name="text-xs font-semibold text-gray-900",
                    ),
                    rx.cond(
                        ok,
                        rx.el.span(
                            ok_label,
                            class_name="text-[10px] font-semibold text-emerald-700 px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-100",
                        ),
                        rx.el.span(
                            pending_label,
                            class_name="text-[10px] font-semibold text-amber-700 px-1.5 py-0.5 rounded bg-amber-50 border border-amber-100",
                        ),
                    ),
                    class_name="flex items-center gap-2 mb-0.5",
                ),
                rx.el.p(
                    description,
                    class_name="text-[11px] text-gray-500 leading-relaxed",
                ),
            ),
            class_name="flex items-start gap-2.5",
        ),
        class_name="p-3 rounded-lg border border-gray-100 bg-gray-50",
    )


def readiness_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "circle-check-big",
                        class_name="h-4 w-4 text-blue-600",
                    ),
                    rx.el.h2(
                        "Hourly Competition Readiness",
                        class_name="text-base font-semibold text-gray-900",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    "Required pieces for the scheduled hourly multi-model prediction workflow",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.cond(
                DashboardState.credentials_ready
                & DashboardState.llm_router_ready
                & DashboardState.has_market_data,
                rx.el.div(
                    rx.icon(
                        "shield-check",
                        class_name="h-3.5 w-3.5 text-emerald-600",
                    ),
                    rx.el.span(
                        "All systems ready",
                        class_name="text-xs font-semibold text-emerald-700",
                    ),
                    class_name="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-100",
                ),
                rx.el.div(
                    rx.icon(
                        "shield-alert",
                        class_name="h-3.5 w-3.5 text-amber-600",
                    ),
                    rx.el.span(
                        "Setup required",
                        class_name="text-xs font-semibold text-amber-700",
                    ),
                    class_name="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50 border border-amber-100",
                ),
            ),
            class_name="flex items-start justify-between gap-3 mb-4 flex-wrap",
        ),
        rx.el.div(
            _step(
                "key",
                "Market Data Credentials",
                "SoSoValue API key configured (SoDEX testnet is public).",
                DashboardState.credentials_ready,
                "Missing key",
                "Configured",
            ),
            _step(
                "database",
                "Live Market Snapshots",
                "BTC, ETH, SOL, AVAX prices fetched from SoSoValue + SoDEX.",
                DashboardState.has_market_data,
                "Awaiting refresh",
                "Live",
            ),
            _step(
                "brain",
                "OpenRouter Prediction Engine",
                "OPENROUTER_API_KEY enables 3-model competition across horizons.",
                DashboardState.llm_router_ready,
                "Missing key",
                "Ready",
            ),
            _step(
                "trophy",
                "Competition Results",
                "At least one prediction batch executed across all models.",
                DashboardState.total_forecasts > 0,
                "No runs yet",
                "Active",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2",
        ),
        rx.el.div(
            rx.icon(
                "clock", class_name="h-3.5 w-3.5 text-blue-600 shrink-0 mt-0.5"
            ),
            rx.el.div(
                rx.el.p(
                    "Hourly cadence",
                    class_name="text-[11px] font-semibold text-gray-900",
                ),
                rx.el.p(
                    rx.cond(
                        DashboardState.last_refresh != "",
                        f"Markets last synced {DashboardState.last_refresh}. Auto-refresh runs every 60 minutes.",
                        "Auto-refresh starts on first load and runs every 60 minutes.",
                    ),
                    class_name="text-[11px] text-gray-600",
                ),
            ),
            class_name="flex items-start gap-2 mt-3 p-3 rounded-lg bg-blue-50 border border-blue-100",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "calendar-clock",
                        class_name="h-3.5 w-3.5 text-blue-600 shrink-0",
                    ),
                    rx.el.p(
                        "Scheduled Competition",
                        class_name="text-[11px] font-semibold text-gray-900",
                    ),
                    class_name="flex items-center gap-1.5 mb-1",
                ),
                rx.el.p(
                    f"Cadence: {DashboardState.forecast_cadence}",
                    class_name="text-[11px] text-gray-600",
                ),
                rx.el.p(
                    rx.cond(
                        DashboardState.next_scheduled_run != "",
                        f"Next run: {DashboardState.next_scheduled_run}",
                        "Next run: pending readiness…",
                    ),
                    class_name="text-[11px] text-gray-600",
                ),
                rx.el.p(
                    rx.cond(
                        DashboardState.last_scheduled_run != "",
                        f"Last scheduled: {DashboardState.last_scheduled_run} ({DashboardState.scheduled_runs_count} total)",
                        "No scheduled runs completed yet",
                    ),
                    class_name="text-[11px] text-gray-500",
                ),
                class_name="flex-1 min-w-0",
            ),
            rx.cond(
                DashboardState.scheduler_ready,
                rx.el.div(
                    rx.el.div(
                        class_name="h-1.5 w-1.5 rounded-full bg-emerald-500"
                    ),
                    rx.el.span(
                        DashboardState.scheduler_status,
                        class_name="text-[10px] font-semibold text-emerald-700 truncate max-w-[200px]",
                    ),
                    class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-emerald-50 border border-emerald-100 shrink-0",
                ),
                rx.el.div(
                    rx.el.div(
                        class_name="h-1.5 w-1.5 rounded-full bg-amber-500"
                    ),
                    rx.el.span(
                        rx.cond(
                            DashboardState.scheduler_status != "",
                            DashboardState.scheduler_status,
                            "Awaiting readiness",
                        ),
                        class_name="text-[10px] font-semibold text-amber-700 truncate max-w-[200px]",
                    ),
                    class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-50 border border-amber-100 shrink-0",
                ),
            ),
            class_name="flex items-start gap-3 mt-2 p-3 rounded-lg bg-white border border-gray-200",
        ),
        class_name="mb-6 p-5 rounded-xl bg-white border border-gray-200",
    )