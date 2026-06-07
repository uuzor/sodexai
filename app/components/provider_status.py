import reflex as rx
from app.states.dashboard_state import DashboardState, ProviderStatus


def status_pill(status: str) -> rx.Component:
    return rx.match(
        status,
        (
            "connected",
            rx.el.div(
                rx.el.div(class_name="h-1.5 w-1.5 rounded-full bg-emerald-500"),
                rx.el.span(
                    "Connected",
                    class_name="text-[11px] font-semibold text-emerald-700",
                ),
                class_name="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-100 w-fit",
            ),
        ),
        (
            "error",
            rx.el.div(
                rx.el.div(class_name="h-1.5 w-1.5 rounded-full bg-red-500"),
                rx.el.span(
                    "Error", class_name="text-[11px] font-semibold text-red-700"
                ),
                class_name="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-red-50 border border-red-100 w-fit",
            ),
        ),
        rx.el.div(
            rx.el.div(class_name="h-1.5 w-1.5 rounded-full bg-amber-500"),
            rx.el.span(
                "Disconnected",
                class_name="text-[11px] font-semibold text-amber-700",
            ),
            class_name="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-amber-50 border border-amber-100 w-fit",
        ),
    )


def provider_row(provider: ProviderStatus) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    rx.cond(
                        provider["kind"] == "Market Data", "database", "brain"
                    ),
                    class_name="h-4 w-4 text-gray-600",
                ),
                class_name="h-9 w-9 rounded-lg bg-gray-50 border border-gray-200 flex items-center justify-center shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    provider["name"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.p(provider["kind"], class_name="text-xs text-gray-500"),
            ),
            class_name="flex items-center gap-3",
        ),
        rx.el.div(
            status_pill(provider["status"]),
            rx.el.p(
                provider["message"], class_name="text-[11px] text-gray-500 mt-1"
            ),
            class_name="text-right",
        ),
        class_name="flex items-center justify-between p-3 border-b border-gray-100 last:border-b-0",
    )


def provider_status_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Provider & Model Status",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Live integration health",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.el.div(
                rx.el.span(
                    f"{DashboardState.connected_count}/{DashboardState.total_providers}",
                    class_name="text-xs font-semibold text-gray-700 tabular-nums",
                ),
                class_name="px-2 py-1 rounded-md bg-gray-50 border border-gray-200",
            ),
            class_name="flex items-center justify-between p-4 border-b border-gray-100",
        ),
        rx.el.div(
            rx.foreach(DashboardState.providers, provider_row),
        ),
        class_name="rounded-xl bg-white border border-gray-200 overflow-hidden",
    )