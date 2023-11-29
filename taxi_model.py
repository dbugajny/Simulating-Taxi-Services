from enum import Enum


class TaxiStatus(Enum):
    GOING_TO_CUSTOMER = 1
    HAS_CUSTOMER = 2
    FREE = 3
    STOPPED = 4


class Taxi:
    def __init__(self, current_vertex: str):
        self.status = TaxiStatus.FREE

        self.current_vertex: str = current_vertex

        self.n_customers_delivered: int = 0

        self.total_income: int = 0
        self.total_distance: int = 0
        self.timer: int = 0
