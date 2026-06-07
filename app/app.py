import reflex as rx
from app.states.dashboard_state import DashboardState
from app.components.sidebar import sidebar
from app.components.header import header
from app.components.market_summary import market_summary
from app.components.forecast_cards import forecast_cards
from app.components.provider_status import provider_status_panel
from app.components.configuration import configuration_section
from app.components.metrics_strip import metrics_strip
from app.components.performance_section import performance_section
from app.components.leaderboard import leaderboard
from app.components.competition_grid import competition_grid
from app.components.readiness_panel import readiness_panel


def banner() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("zap", class_name="h-4 w-4 text-blue-600 shrink-0"),
            rx.el.div(
                rx.el.p(
                    "Live prediction engine active",
                    class_name="text-xs font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Real market data flows from SoSoValue + SoDEX; OpenRouter generates structured forecasts across 5m / 30m / 6h horizons. Matured predictions are scored against subsequent live prices.",
                    class_name="text-[11px] text-gray-600",
                ),
            ),
            class_name="flex items-start gap-2.5",
        ),
        class_name="px-4 py-2.5 rounded-xl bg-blue-50 border border-blue-100 mb-5",
    )


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            sidebar(),
            rx.el.div(
                header(),
                rx.el.div(
                    banner(),
                    banner(),
                    metrics_strip(),
                    readiness_panel(),
                    market_summary(),
                    rx.el.div(
                        rx.el.div(
                            forecast_cards(),
                            class_name="lg:col-span-2",
                        ),
                        rx.el.div(
                            provider_status_panel(),
                            class_name="lg:col-span-1",
                        ),
                        class_name="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6",
                    ),
                    competition_grid(),
                    leaderboard(),
                    performance_section(),
                    configuration_section(),
                    class_name="p-6 max-w-[1400px] mx-auto",
                ),
                class_name="flex-1 min-w-0",
            ),
            class_name="flex min-h-screen bg-gray-50",
        ),
        class_name="font-['Inter'] text-gray-900 antialiased",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(
    index,
    route="/",
    on_load=[
        DashboardState.refresh_market_data,
        DashboardState.start_auto_refresh,
    ],
)