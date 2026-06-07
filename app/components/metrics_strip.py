import reflex as rx
from app.states.dashboard_state import DashboardState


def metric_card(
    icon: str, label: str, value, sublabel: str, accent: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name=f"h-4 w-4 {accent}"),
                class_name="h-9 w-9 rounded-lg bg-gray-50 border border-gray-200 flex items-center justify-center",
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


def metrics_strip() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            metric_card(
                "target",
                "Active Target",
                DashboardState.active_target,
                "ASSET",
                "text-blue-600",
            ),
            metric_card(
                "clock",
                "Cadence",
                DashboardState.forecast_cadence,
                "SCHEDULE",
                "text-purple-600",
            ),
            metric_card(
                "activity",
                "Providers",
                f"{DashboardState.connected_count}/{DashboardState.total_providers}",
                "STATUS",
                "text-emerald-600",
            ),
            metric_card(
                "shield",
                "SoSoValue Key",
                rx.cond(
                    DashboardState.credentials_ready, "Configured", "Missing"
                ),
                "SECURITY",
                "text-amber-600",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3",
        ),
        class_name="mb-6",
    )