import reflex as rx


class PerformanceState(rx.State):
    filter_asset: str = "All"
    filter_horizon: str = "All"
    filter_accuracy: str = "All"
    filter_model: str = "All"
    filter_model_slot: str = "All"

    @rx.event
    def set_filter_asset(self, value: str):
        self.filter_asset = value

    @rx.event
    def set_filter_horizon(self, value: str):
        self.filter_horizon = value

    @rx.event
    def set_filter_accuracy(self, value: str):
        self.filter_accuracy = value

    @rx.event
    def set_filter_model(self, value: str):
        self.filter_model = value

    @rx.event
    def set_filter_model_slot(self, value: str):
        self.filter_model_slot = value

    @rx.event
    def reset_filters(self):
        self.filter_asset = "All"
        self.filter_horizon = "All"
        self.filter_accuracy = "All"
        self.filter_model = "All"
        self.filter_model_slot = "All"