from infrastructure.data_providers.graph.cycle import Cycle


class CycleManager:
    """
    Manages the creation and storage of trading cycles.
    """

    def __init__(self):
        self.cycle_managers: dict[str, Cycle] = {}
    